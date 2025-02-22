"""Base LLM provider implementation.

This module provides the base implementation for LLM (Language Model) providers.
It combines functionality from both the core provider base and service provider.
"""

from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

from pepperpy.core.messages import ProviderMessage, ProviderResponse
from pepperpy.core.metrics import MetricsManager
from pepperpy.core.monitoring import logger
from pepperpy.providers.base import BaseProvider, ProviderConfig


class LLMMessage(BaseModel):
    """Language model message.

    Attributes:
        role: Message role (system, user, assistant)
        content: Message content
        name: Optional name for the message sender
    """

    role: str
    content: str
    name: Optional[str] = None


class LLMConfig(ProviderConfig):
    """Base configuration for LLM providers.

    Attributes:
        model: Model identifier to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        stop_sequences: Optional stop sequences
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
    """

    model: str = Field(description="Model identifier to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens to generate")
    stop_sequences: list[str] | None = Field(
        default=None, description="Optional stop sequences"
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class LLMResponse(BaseModel):
    """Language model response.

    Attributes:
        id: Response identifier
        content: Generated content
        model: Model used for generation
        usage: Token usage statistics
        finish_reason: Reason for completion
    """

    id: UUID
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: Optional[str] = None


class LLMProvider(BaseProvider):
    """Base class for LLM providers.

    This class provides common functionality for providers that interact
    with LLM services.
    """

    def __init__(self, config: LLMConfig) -> None:
        """Initialize LLM provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._metrics = MetricsManager.get_instance()
        logger.debug("Initialized LLM provider with config: %s", config)

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        """
        try:
            # Initialize service connection
            await self._initialize_service()
            self._metrics.increment("provider.llm.successful_initializations")
            logger.info("LLM provider initialized successfully")
            self._initialized = True
        except Exception as e:
            self._metrics.increment("provider.llm.initialization_errors")
            logger.error("Failed to initialize LLM provider: %s", e)
            raise

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should be called when the provider is no longer needed.
        """
        try:
            # Clean up service connection
            await self._cleanup_service()
            self._metrics.increment("provider.llm.successful_cleanups")
            logger.info("LLM provider cleaned up successfully")
            self._initialized = False
        except Exception as e:
            self._metrics.increment("provider.llm.cleanup_errors")
            logger.error("Failed to clean up LLM provider: %s", e)
            raise

    @abstractmethod
    async def _initialize_service(self) -> None:
        """Initialize service connection.

        This method should be implemented by subclasses to handle
        service-specific initialization.
        """
        pass

    @abstractmethod
    async def _cleanup_service(self) -> None:
        """Clean up service connection.

        This method should be implemented by subclasses to handle
        service-specific cleanup.
        """
        pass

    @abstractmethod
    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process a provider message.

        Args:
            message: Provider message to process

        Returns:
            Provider response or async generator of responses

        Raises:
            ProviderError: If message processing fails
        """
        pass

    @abstractmethod
    async def embed(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        **kwargs: Any,
    ) -> list[float]:
        """Generate embeddings for the given text.

        Args:
            text: Text to generate embeddings for
            model: Optional model to use for embeddings
            dimensions: Optional number of dimensions for embeddings
            **kwargs: Additional model-specific parameters

        Returns:
            List of embedding values

        Raises:
            ProviderError: If embedding generation fails
        """
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from the language model.

        Args:
            messages: List of messages for context
            **kwargs: Additional provider-specific parameters

        Returns:
            Model response

        Raises:
            ProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def validate(self) -> None:
        """Validate provider configuration and state.

        Raises:
            ConfigurationError: If validation fails
        """
        pass

    @abstractmethod
    async def get_token_count(self, text: str) -> int:
        """Get the number of tokens in the text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens

        Raises:
            ProviderError: If token counting fails
        """
        pass
