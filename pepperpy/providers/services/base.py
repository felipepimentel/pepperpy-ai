"""Base classes for service providers.

This module contains the base classes and protocols for implementing service providers
in the Pepperpy framework.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from typing import Any, Protocol, TypeVar, runtime_checkable

from pepperpy.common.errors import ProviderError
from pepperpy.monitoring import logger

from ..domain import ProviderAPIError, ProviderRateLimitError
from ..provider import Provider, ProviderConfig

T = TypeVar("T", covariant=True)


class BaseProviderMixin(Provider):
    """Base mixin with common provider functionality."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the base provider mixin."""
        super().__init__(config)
        self._logger = logger.bind(provider=self.__class__.__name__)

    async def _handle_api_error(
        self, error: Exception, context: dict[str, Any]
    ) -> None:
        """Handle API errors in a standardized way.

        Args:
            error: The original error
            context: Additional context about the error
        """
        self._logger.error("API error occurred", error=str(error), **context)
        if "rate" in str(error).lower():
            raise ProviderRateLimitError(
                message=str(error),
                provider_type=self.config.provider_type,
                details=context,
            ) from error
        raise ProviderAPIError(
            message=str(error),
            provider_type=self.config.provider_type,
            details=context,
        ) from error


@runtime_checkable
class ContentExtractor(Protocol):
    """Protocol for content extraction functions."""

    def __call__(self, chunk: Any) -> str:
        """Extract content from a chunk.

        Args:
            chunk: The chunk to extract content from

        Returns:
            The extracted content as a string
        """
        ...


@runtime_checkable
class EmbedFunction(Protocol):
    """Protocol for embedding functions."""

    def __call__(self, text: str, model: str) -> Awaitable[list[float]]:
        """Generate embeddings for text using a model.

        Args:
            text: The text to generate embeddings for
            model: The model to use for generating embeddings

        Returns:
            A list of embedding values
        """
        ...


class StreamingMixin(BaseProviderMixin):
    """Mixin for handling streaming responses."""

    async def _handle_streaming_response(
        self,
        response: AsyncIterator[Any],
        extract_content: ContentExtractor,
    ) -> AsyncGenerator[str, None]:
        """Handle streaming responses in a standardized way.

        Args:
            response: The streaming response
            extract_content: Function to extract content from each chunk

        Yields:
            Extracted content from each chunk
        """
        try:
            async for chunk in response:
                content = extract_content(chunk)
                if content:
                    yield content
        except Exception as e:
            await self._handle_api_error(e, {"streaming": True})


class EmbeddingMixin(BaseProviderMixin):
    """Mixin for handling embeddings."""

    async def _handle_embedding_request(
        self,
        text: str,
        model: str,
        embed_func: EmbedFunction,
    ) -> list[float]:
        """Handle embedding requests in a standardized way.

        Args:
            text: Text to embed
            model: Model to use for embedding
            embed_func: Function to perform the embedding

        Returns:
            List of embedding values
        """
        try:
            result = await embed_func(text, model)
            return result
        except Exception as e:
            await self._handle_api_error(e, {"text": text, "model": model})
            raise  # This will never be reached, but makes type checking happy


@runtime_checkable
class ProviderCallback(Protocol[T]):
    """Protocol for provider callbacks."""

    async def __call__(self, *args: Any, **kwargs: Any) -> T:
        """Execute the callback.

        Args:
            *args: Positional arguments for the callback
            **kwargs: Keyword arguments for the callback

        Returns:
            The result of the callback execution
        """
        ...


@runtime_checkable
class ProviderStreamCallback(Protocol[T]):
    """Protocol for streaming provider callbacks."""

    def __call__(self, *args: Any, **kwargs: Any) -> AsyncGenerator[T, None]:
        """Execute the streaming callback.

        Args:
            *args: Positional arguments for the callback
            **kwargs: Keyword arguments for the callback

        Returns:
            An async generator of items from the API stream
        """
        ...


class BaseProvider(Provider, ABC):
    """Base class for all providers."""

    @abstractmethod
    async def _call_api(
        self,
        callback: ProviderCallback[T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Call the provider API with error handling."""
        raise NotImplementedError

    @abstractmethod
    def _stream_api(
        self,
        callback: ProviderStreamCallback[T],
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator[T]:
        """Stream from the provider API with error handling.

        Args:
            callback: The API callback to execute
            *args: Positional arguments for the callback
            **kwargs: Keyword arguments for the callback

        Returns:
            An async iterator of items from the API stream

        Raises:
            ProviderAPIError: If the API call fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        raise NotImplementedError
