"""Base provider interface for the Pepperpy framework.

This module defines the core interfaces and base classes that all providers
must implement, ensuring consistent behavior across different implementations.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from types import TracebackType
from typing import (
    Any,
    Dict,
    List,
    NotRequired,
    Optional,
    Protocol,
    TypedDict,
    TypeVar,
    Union,
)
from uuid import UUID

from pydantic import BaseModel

from pepperpy.core.errors import ValidationError
from pepperpy.core.types import Message, Response
from pepperpy.monitoring import bind_logger, logger
from pepperpy.providers.domain import (
    ProviderError,
)

T = TypeVar("T", covariant=True)

# Type alias for provider callback
ProviderCallback = Callable[[Dict[str, Any]], None]

# Valid provider types
VALID_PROVIDER_TYPES = frozenset({
    "services.openai",
    "services.openrouter",
    "services.anthropic",
    "services.gemini",
    "services.perplexity",
    "services.stackspot",
})

# Configure logger
logger = bind_logger(module="providers.base")


class LogContext(TypedDict, total=True):
    """Type definition for logging context information."""

    error: NotRequired[str | Exception]
    status: NotRequired[str]
    model: NotRequired[str]
    provider: NotRequired[str]
    duration: NotRequired[float]
    tokens: NotRequired[int]
    request_id: NotRequired[str]
    extra: NotRequired[Dict[str, Union[str, int, float, bool]]]


class Message(BaseModel):
    """A message that can be exchanged with providers."""

    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class Response(BaseModel):
    """A response from a provider."""

    id: UUID
    content: str
    metadata: Optional[Dict[str, Any]] = None


class LoggerProtocol(Protocol):
    """Protocol for logger interface."""

    def error(self, message: str, **context: str) -> None:
        """Log an error message.

        Args:
        ----
            message: The error message to log.
            **context: Additional context information as string values.

        """
        ...

    def info(self, message: str, **context: str) -> None:
        """Log an info message.

        Args:
        ----
            message: The info message to log.
            **context: Additional context information as string values.

        """
        ...

    def debug(self, message: str, **context: str) -> None:
        """Log a debug message.

        Args:
        ----
            message: The debug message to log.
            **context: Additional context information as string values.

        """
        ...

    def warning(self, message: str, **context: str) -> None:
        """Log a warning message.

        Args:
        ----
            message: The warning message to log.
            **context: Additional context information as string values.

        """
        ...


# Type alias for provider configuration values
type ProviderConfigValue = str | int | float | bool | list[str] | dict[str, Any]


class ExtraConfig(TypedDict, total=False):
    """Additional provider configuration options."""

    model_params: NotRequired[dict[str, ProviderConfigValue]]
    api_params: NotRequired[dict[str, ProviderConfigValue]]
    custom_settings: NotRequired[dict[str, ProviderConfigValue]]


class ProviderConfig(BaseModel):
    """Configuration for a provider."""

    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    stop_sequences: Optional[List[str]] = None
    timeout: float = 30.0
    max_retries: int = 3


class GenerateKwargs(BaseModel):
    """Keyword arguments for generate method."""

    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    stop_sequences: Optional[List[str]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None


class ProviderKwargs(TypedDict, total=False):
    """Type definition for provider-specific keyword arguments."""

    model: str
    temperature: float
    max_tokens: int
    stop: list[str] | None
    stop_sequences: list[str] | None


class EmbeddingKwargs(TypedDict, total=False):
    """Keyword arguments for embedding methods."""

    model: NotRequired[str]
    model_params: NotRequired[dict[str, Any]]
    batch_size: NotRequired[int]
    encoding_format: NotRequired[str]


class StreamKwargs(BaseModel):
    """Keyword arguments for stream method."""

    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    chunk_size: Optional[int] = None
    buffer_size: Optional[int] = None


class BaseProvider(ABC):
    """Base class for provider implementations."""

    def __init__(self, config: Union[Dict[str, Any], ProviderConfig]) -> None:
        """Initialize the provider.

        Args:
        ----
            config: Provider configuration.

        """
        self.config = (
            config if isinstance(config, ProviderConfig) else ProviderConfig(**config)
        )
        self.name = self.__class__.__name__
        self._initialized = False
        self._logger = bind_logger(provider=self.name)

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self._initialized:
            raise ValidationError("Provider already initialized")
        self._initialized = True
        self._logger.info("Provider initialized successfully")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self._initialized:
            raise ValidationError("Provider not initialized")
        self._initialized = False
        self._logger.info("Provider cleaned up successfully")

    def _ensure_initialized(self) -> None:
        """Ensure provider is initialized.

        Raises
        ------
            ValidationError: If provider is not initialized

        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

    @abstractmethod
    async def send_message(self, message: str) -> Response:
        """Send a message and get a response.

        Args:
        ----
            message: Message to send.

        Returns:
        -------
            Response: Provider response.

        """
        raise NotImplementedError

    @abstractmethod
    async def generate(self, messages: List[Message], **kwargs: Any) -> Response:
        """Generate a response from the provider.

        Args:
        ----
            messages: List of messages to process.
            **kwargs: Additional keyword arguments.

        Returns:
        -------
            Response: Provider response.

        """
        self._ensure_initialized()
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self, messages: List[Message], **kwargs: Any
    ) -> AsyncGenerator[Response, None]:
        """Stream responses from the provider.

        Args:
        ----
            messages: List of messages to process.
            **kwargs: Additional keyword arguments.

        Yields:
        ------
            Response: Provider responses.

        """
        self._ensure_initialized()
        raise NotImplementedError

    def _stringify_context(
        self, context: dict[str, str | int | float | bool]
    ) -> dict[str, str]:
        """Convert all context values to strings.

        Args:
        ----
            context: Dictionary with mixed-type values

        Returns:
        -------
            Dictionary with all string values

        """
        return {k: str(v) for k, v in context.items()}

    async def _handle_api_error(
        self, error: Exception, context: dict[str, str | int | float | bool]
    ) -> None:
        """Handle API errors in a consistent way.

        Args:
        ----
            error: The original error
            context: Additional context about the error

        Raises:
        ------
            ProviderError: With appropriate error details

        """
        log_context = self._stringify_context({
            "error": str(error),
            "provider": self.name,
            **context,
        })
        self._logger.error("API error occurred", **log_context)
        raise ProviderError(
            message=str(error), provider_type=self.name, details=context
        ) from error

    def _check_initialized(self) -> None:
        """Check if provider is initialized.

        Raises
        ------
            RuntimeError: If provider is not initialized

        """
        if not self._initialized:
            raise RuntimeError(
                f"Provider {self.name} not initialized. Call initialize() first."
            )

    async def __aenter__(self) -> "BaseProvider":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.cleanup()

    @abstractmethod
    async def chat_completion(
        self,
        model: str,
        messages: List[Message],
        **kwargs: Any,
    ) -> str:
        """Run a chat completion with the given parameters.

        Args:
        ----
            model: The model to use
            messages: The messages to send to the model
            **kwargs: Additional parameters for the model

        Returns:
        -------
            The model's response

        """
        raise NotImplementedError


class Provider(ABC):
    """Base class for AI providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the provider.

        Args:
        ----
            config: Optional configuration for the provider.

        """
        self.config = config or {}

    @abstractmethod
    async def generate(
        self, prompt: str, parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a response for the given prompt.

        Args:
        ----
            prompt: The prompt to generate a response for.
            parameters: Optional parameters for the generation.

        Returns:
        -------
            The generated response.

        """
        pass
