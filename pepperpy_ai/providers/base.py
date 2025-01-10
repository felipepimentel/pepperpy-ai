"""Base provider implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, Generic, Protocol, TypeVar, Optional, cast, AsyncIterator
from datetime import datetime, timedelta
import logging
import asyncio
import functools
import random

from pepperpy_core.exceptions import PepperpyError
from pepperpy_core.telemetry import TelemetryManager
from pepperpy_core.utils.backoff import exponential_backoff

from ..ai_types import AIResponse, AIMessage
from ..exceptions import ProviderError, ValidationError
from .config import ProviderConfig
from .exceptions import (
    ProviderAPIError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from .types import (
    ProviderCapabilities,
    ProviderMetadata,
    ProviderResponse,
    ProviderUsage,
)
from ..types import JsonDict, MessageRole

logger = logging.getLogger(__name__)

ConfigT = TypeVar("ConfigT", bound=ProviderConfig)
TokenCounter = Callable[[str], int]

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
) -> Callable:
    """Retry decorator with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Backoff multiplier
        jitter: Whether to add random jitter
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self: "BaseProvider", *args: Any, **kwargs: Any) -> Any:
            retries = 0
            delay = initial_delay
            
            while True:
                try:
                    return await func(self, *args, **kwargs)
                except ProviderRateLimitError as e:
                    retry_after = getattr(e, "retry_after", None)
                    if retry_after:
                        await asyncio.sleep(retry_after)
                        continue
                    
                    if retries >= max_retries:
                        raise
                        
                    delay = min(
                        max_delay,
                        delay * backoff_factor * (1 + random.random() * 0.1 if jitter else 1)
                    )
                    await asyncio.sleep(delay)
                    retries += 1
                except (ProviderAPIError, ProviderTimeoutError) as e:
                    if retries >= max_retries:
                        raise
                        
                    delay = min(
                        max_delay,
                        delay * backoff_factor * (1 + random.random() * 0.1 if jitter else 1)
                    )
                    await asyncio.sleep(delay)
                    retries += 1
                except Exception:
                    raise
        return wrapper
    return decorator

class BaseProvider(Generic[ConfigT], ABC):
    """Base provider implementation.
    
    This class provides the foundation for all AI providers.
    It handles initialization, cleanup, and common provider operations.
    
    Attributes:
        config: Provider configuration
        metadata: Provider metadata
        usage: Provider usage statistics
        _initialized: Provider initialization state
        _last_request: Timestamp of last request
        _request_count: Number of requests made
        _lock: Provider lock for thread safety
        _telemetry: Telemetry manager for monitoring
        _rate_limiter: Rate limiter for request throttling
    """

    def __init__(self, config: ConfigT) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.metadata = ProviderMetadata(
            name=config.name,
            version=getattr(config, "version", "1.0.0"),
            description=getattr(config, "description", ""),
            settings=config.to_dict(),
        )
        self.usage = ProviderUsage()
        self._initialized = False
        self._last_request: Optional[datetime] = None
        self._request_count: int = 0
        self._lock = asyncio.Lock()
        self._telemetry = TelemetryManager()
        self._rate_limiter = asyncio.Semaphore(
            self.capabilities.max_requests_per_minute or 60
        )

    async def _acquire_rate_limit(self) -> None:
        """Acquire rate limit semaphore.
        
        This ensures we don't exceed the provider's rate limit.
        """
        try:
            await asyncio.wait_for(
                self._rate_limiter.acquire(),
                timeout=self.config.settings.get("request_timeout", 30.0)
            )
        except asyncio.TimeoutError:
            raise ProviderRateLimitError(
                provider=self.config.provider,
                retry_after=60
            )

    async def _release_rate_limit(self) -> None:
        """Release rate limit semaphore."""
        self._rate_limiter.release()

    async def _track_metrics(self, operation: str, **metrics: Any) -> None:
        """Track provider metrics.
        
        Args:
            operation: Operation being tracked
            **metrics: Metrics to record
        """
        await self._telemetry.record_metrics(
            namespace="provider",
            operation=operation,
            provider=self.config.provider,
            model=self.config.model,
            **metrics
        )

    async def _handle_error(
        self,
        error: Exception,
        operation: str,
        **context: Any
    ) -> None:
        """Handle provider error.
        
        Args:
            error: Error that occurred
            operation: Operation that failed
            **context: Additional error context
        """
        # Track error metrics
        await self._track_metrics(
            operation=operation,
            error=True,
            error_type=error.__class__.__name__,
            **context
        )

        # Log error with context
        logger.error(
            f"Provider error in {operation}",
            extra={
                "provider": self.config.provider,
                "operation": operation,
                "error": str(error),
                "context": context
            }
        )

        # Convert to appropriate error type
        if isinstance(error, PepperpyError):
            raise error
        
        raise ProviderError(
            str(error),
            provider=self.config.provider,
            operation=operation,
            cause=error,
            **context
        )

    @retry_with_backoff()
    async def complete(self, prompt: str) -> AIResponse:
        """Complete prompt.
        
        Args:
            prompt: Prompt to complete
            
        Returns:
            AI response
            
        Raises:
            ProviderError: If completion fails
            ProviderValidationError: If prompt is invalid
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
            ProviderAuthError: If authentication fails
            ProviderAPIError: If API call fails
        """
        try:
            await self._acquire_rate_limit()
            self._validate_prompt(prompt)
            
            start_time = datetime.now()
            response = await self._complete(prompt)
            latency = (datetime.now() - start_time).total_seconds()
            
            await self._track_request(
                tokens=getattr(response, "tokens_used", 0),
                latency=latency
            )
            
            return response
        except Exception as e:
            await self._handle_error(e, "complete", prompt=prompt)
            raise  # Re-raise to satisfy return type

    @retry_with_backoff()
    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses.
        
        Args:
            prompt: Prompt to stream
            
        Yields:
            AI response chunks
            
        Raises:
            ProviderError: If streaming fails
            ProviderValidationError: If prompt is invalid
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
            ProviderAuthError: If authentication fails
            ProviderAPIError: If API call fails
        """
        try:
            await self._acquire_rate_limit()
            self._validate_prompt(prompt)
            
            start_time = datetime.now()
            total_tokens = 0
            
            async for response in await self._stream(prompt):
                total_tokens += getattr(response, "tokens_used", 0)
                yield response
            
            latency = (datetime.now() - start_time).total_seconds()
            await self._track_request(
                tokens=total_tokens,
                latency=latency
            )
        except Exception as e:
            await self._handle_error(e, "stream", prompt=prompt)
            raise StopAsyncIteration
        finally:
            await self._release_rate_limit()

    @abstractmethod
    async def _complete(self, prompt: str) -> AIResponse:
        """Internal completion implementation.
        
        Args:
            prompt: Prompt to complete
            
        Returns:
            AI response
        """
        pass

    @abstractmethod
    async def _stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Internal streaming implementation.
        
        Args:
            prompt: Prompt to stream
            
        Yields:
            AI response chunks
        """
        pass

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        pass

    @property
    def token_counter(self) -> Optional[TokenCounter]:
        """Get token counter function.
        
        Returns:
            Token counter function if available, None otherwise
        """
        counter = getattr(self, "count_tokens", None)
        return counter if callable(counter) else None

    async def initialize(self) -> None:
        """Initialize provider.
        
        Raises:
            ProviderError: If initialization fails
        """
        if self._initialized:
            return
        
        try:
            await self._validate_config()
            await self._setup()
            self._initialized = True
            logger.info(f"Initialized provider: {self.config.name}")
        except Exception as e:
            error = ProviderError(
                "Failed to initialize provider",
                provider=self.config.name,
                operation="initialize",
                cause=e
            )
            logger.error(str(error))
            raise error

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        if not self._initialized:
            return
        
        try:
            await self._teardown()
            logger.info(f"Cleaned up provider: {self.config.name}")
        except Exception as e:
            logger.error(f"Error cleaning up provider: {e}")
        finally:
            self._initialized = False

    @asynccontextmanager
    async def session(self) -> AsyncIterator[None]:
        """Provider session context manager.
        
        Example:
            async with provider.session():
                response = await provider.complete("Hello")
                
        Raises:
            ProviderError: If session initialization fails
        """
        try:
            await self.initialize()
            yield
        finally:
            await self.cleanup()

    async def _validate_config(self) -> None:
        """Validate provider configuration.
        
        Raises:
            ProviderValidationError: If configuration is invalid
        """
        required_fields = {"name", "api_key", "model"}
        config_dict = cast(dict[str, Any], self.config)
        missing = required_fields - set(config_dict)
        if missing:
            raise ProviderValidationError(
                f"Missing required configuration fields: {missing}",
                provider=self.config.name,
                field="config",
                value=missing,
                constraints={"required_fields": list(required_fields)}
            )

    @abstractmethod
    async def _setup(self) -> None:
        """Setup provider resources.
        
        Raises:
            ProviderError: If setup fails
        """
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown provider resources.
        
        Raises:
            ProviderError: If teardown fails
        """
        pass

    async def _track_request(
        self,
        tokens: int = 0,
        latency: float = 0.0,
        error: bool = False
    ) -> None:
        """Track request metrics.
        
        Args:
            tokens: Tokens used in request
            latency: Request latency in seconds
            error: Whether request resulted in error
        """
        async with self._lock:
            self._last_request = datetime.now()
            self._request_count += 1
            self.usage.update(tokens=tokens, latency=latency, error=error)

    def _validate_prompt(self, prompt: str) -> None:
        """Validate prompt.
        
        Args:
            prompt: Prompt to validate
            
        Raises:
            ProviderValidationError: If prompt is invalid
        """
        if not prompt:
            raise ProviderValidationError(
                "Prompt cannot be empty",
                provider=self.config.name,
                field="prompt"
            )
        
        # Check token limit if provider supports it
        counter = self.token_counter
        if counter is not None:
            token_count = counter(prompt)
            if token_count > self.capabilities.max_tokens:
                raise ProviderValidationError(
                    f"Prompt exceeds token limit: {token_count} > {self.capabilities.max_tokens}",
                    provider=self.config.name,
                    field="prompt",
                    value=token_count,
                    constraints={"max_tokens": self.capabilities.max_tokens}
                )

    def _check_rate_limit(self) -> None:
        """Check rate limit.
        
        Raises:
            ProviderRateLimitError: If rate limit is exceeded
        """
        if not self.capabilities.max_requests_per_minute:
            return
            
        if not self._last_request:
            return
            
        time_diff = datetime.now() - self._last_request
        if time_diff < timedelta(minutes=1):
            requests_per_minute = self._request_count / time_diff.total_seconds() * 60
            if requests_per_minute > self.capabilities.max_requests_per_minute:
                retry_after = int(60 - time_diff.total_seconds())
                raise ProviderRateLimitError(
                    provider=self.config.name,
                    retry_after=retry_after
                )

    async def get_embedding(self, text: str) -> list[float]:
        """Get text embedding.
        
        Args:
            text: Text to embed
            
        Returns:
            Text embedding
            
        Raises:
            ProviderError: If embedding fails
            ProviderValidationError: If text is invalid
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
            ProviderAuthError: If authentication fails
            ProviderAPIError: If API call fails
        """
        if not self.capabilities.embeddings:
            raise ProviderError(
                "Provider does not support embeddings",
                provider=self.config.name,
                operation="get_embedding"
            )
        return []

    async def call_function(
        self,
        prompt: str,
        functions: list[JsonDict],
    ) -> AIMessage:
        """Call function.
        
        Args:
            prompt: Prompt to process
            functions: Available functions
            
        Returns:
            Function call response
            
        Raises:
            ProviderError: If function call fails
            ProviderValidationError: If prompt or functions are invalid
            ProviderRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
            ProviderAuthError: If authentication fails
            ProviderAPIError: If API call fails
        """
        if not self.capabilities.functions:
            raise ProviderError(
                "Provider does not support functions",
                provider=self.config.name,
                operation="call_function"
            )
        return AIMessage(role=MessageRole.FUNCTION, content="")
