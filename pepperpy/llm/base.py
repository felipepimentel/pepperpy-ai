"""Base LLM provider module.

This module defines the base classes and interfaces for LLM providers.
"""

from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel, Field

from pepperpy.core.common.providers.unified import BaseProvider, ProviderConfig
from pepperpy.core.metrics import MetricsManager

    """Language model message.

    Attributes:
        role: Message role (system, user, assistant)
        content: Message content
        name: Optional name for the message sender
    """
class LLMMessage(BaseModel):
    """LLM message."""

    role: str
    content: str
    name: str | None = None


class LLMResponse(BaseModel):
    """LLM response."""

    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str | None = None


class LLMProvider(BaseProvider):
    """Base class for LLM providers."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.metrics = MetricsManager()

    @abstractmethod
    async def process_message(
        self,
        message: LLMMessage,
    ) -> LLMResponse | AsyncGenerator[LLMResponse, None]:
        """Process a provider message.

        Args:
            message: Provider message

        Returns:
            Provider response or async generator of responses
        """
        pass

    @abstractmethod
    async def embed(
        self,
        text: str,
        *,
        model: str | None = None,
        dimensions: int | None = None,
        **kwargs: Any,
    ) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Input text
            model: Model to use for embeddings
            dimensions: Number of dimensions for embeddings
            **kwargs: Additional provider-specific arguments

        Returns:
            Text embeddings
        """
        pass

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response from messages.

        Args:
            messages: Input messages
            **kwargs: Additional provider-specific arguments

        Returns:
            Generated response
        """
        pass
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
    ) -> ProviderResponse | AsyncGenerator[ProviderResponse, None]:
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
        model: str | None = None,
        dimensions: int | None = None,
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
        messages: list[LLMMessage],
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
