"""OpenAI provider implementation for the Pepperpy framework.

This module implements the OpenAI provider, supporting chat completions and embeddings
using OpenAI's API. It handles streaming responses, rate limiting, and proper error
propagation.

The provider supports:
- Chat completions with GPT models
- Text embeddings with Ada
- Streaming responses
- Rate limit handling
- Proper error propagation

Typical usage example:
    >>> from pepperpy.providers import ProviderConfig
    >>> from pepperpy.providers.services.openai import OpenAIProvider
    >>> config = ProviderConfig(
    ...     provider_type="openai",
    ...     api_key="your-api-key",
    ...     model="gpt-3.5-turbo"
    ... )
    >>> async with OpenAIProvider(config) as provider:
    ...     response = await provider.complete(
    ...         "Translate to French: Hello world",
    ...         temperature=0.3
    ...     )
    "Bonjour le monde"
"""

from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from typing import Any, Optional, TypeVar, cast

import openai
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.create_embedding_response import CreateEmbeddingResponse
from openai.types.embedding import Embedding
from pydantic import SecretStr

from pepperpy.common.errors import ProviderError
from pepperpy.monitoring import logger
from pepperpy.providers.domain import (
    ProviderAPIError,
    ProviderInitError,
    ProviderRateLimitError,
)

from ..provider import Provider, ProviderConfig
from .base import (
    BaseProvider,
    ContentExtractor,
    EmbeddingMixin,
    ProviderCallback,
    ProviderStreamCallback,
    StreamingMixin,
)

# Constants
DEFAULT_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"

T = TypeVar("T")


class OpenAIProvider(StreamingMixin, EmbeddingMixin, BaseProvider):
    """OpenAI provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the OpenAI provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._client: AsyncOpenAI | None = None

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            api_key = self.config.api_key
            if not isinstance(api_key, SecretStr):
                raise ProviderInitError("API key must be a SecretStr")

            self._client = AsyncOpenAI(api_key=api_key.get_secret_value())
            await self._validate_client()
        except Exception as e:
            raise ProviderInitError(f"Failed to initialize OpenAI client: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.close()
            self._client = None

    async def _validate_client(self) -> None:
        """Validate the OpenAI client configuration."""
        if not self._client:
            raise ProviderInitError("OpenAI client not initialized")

        try:
            models = await self._client.models.list()
            if not models.data:
                raise ProviderInitError("No models available")
        except openai.APIError as e:
            raise ProviderInitError(f"Failed to validate OpenAI client: {e}") from e

    async def _call_api(
        self,
        callback: ProviderCallback[T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Call the OpenAI API with error handling.

        Args:
            callback: The API callback to execute
            *args: Positional arguments for the callback
            **kwargs: Keyword arguments for the callback

        Returns:
            The result of the API call

        Raises:
            ProviderAPIError: If the API call fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        try:
            return await callback(*args, **kwargs)
        except openai.RateLimitError as e:
            raise ProviderRateLimitError(
                message=str(e),
                provider_type=self.config.provider_type,
                details={"args": args, "kwargs": kwargs},
            ) from e
        except openai.APIError as e:
            raise ProviderAPIError(
                message=str(e),
                provider_type=self.config.provider_type,
                details={"args": args, "kwargs": kwargs},
            ) from e

    async def _stream_api(
        self,
        callback: ProviderStreamCallback[T],
        *args: Any,
        **kwargs: Any,
    ) -> AsyncGenerator[T, None]:
        """Stream from the OpenAI API with error handling.

        Args:
            callback: The API callback to execute
            *args: Positional arguments for the callback
            **kwargs: Keyword arguments for the callback

        Returns:
            An async generator of items from the API stream

        Raises:
            ProviderAPIError: If the API call fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        try:
            async for item in callback(*args, **kwargs):
                yield item
        except openai.RateLimitError as e:
            raise ProviderRateLimitError(
                message=str(e),
                provider_type=self.config.provider_type,
                details={"args": args, "kwargs": kwargs},
            ) from e
        except openai.APIError as e:
            raise ProviderAPIError(
                message=str(e),
                provider_type=self.config.provider_type,
                details={"args": args, "kwargs": kwargs},
            ) from e

    def _extract_chat_content(self, chunk: ChatCompletionChunk) -> str:
        """Extract content from a chat completion chunk.

        Args:
            chunk: The chat completion chunk

        Returns:
            The extracted content
        """
        if not chunk.choices:
            return ""
        delta = chunk.choices[0].delta
        if not delta.content:
            return ""
        return delta.content

    async def chat(
        self,
        messages: list[ChatCompletionMessageParam],
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None] | str:
        """Generate chat completions.

        Args:
            messages: List of messages in the conversation
            stream: Whether to stream the response
            **kwargs: Additional arguments for the API

        Returns:
            Generated text or stream of text chunks

        Raises:
            ProviderAPIError: If the API call fails
            ProviderRateLimitError: If rate limit is exceeded
            ProviderInitError: If the client is not initialized
        """
        if not self._client:
            raise ProviderInitError("OpenAI client not initialized")

        client = self._client  # Type assertion to help mypy
        assert client is not None

        if stream:
            return self._handle_streaming_response(
                self._stream_api(
                    cast(
                        ProviderStreamCallback[ChatCompletionChunk],
                        client.chat.completions.create,
                    ),
                    messages=messages,
                    model=self.config.model,
                    stream=True,
                    **kwargs,
                ),
                self._extract_chat_content,
            )

        response: ChatCompletion = await self._call_api(
            cast(ProviderCallback[ChatCompletion], client.chat.completions.create),
            messages=messages,
            model=self.config.model,
            stream=False,
            **kwargs,
        )

        if not response.choices:
            return ""
        content = response.choices[0].message.content
        return content if content else ""

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for
            **kwargs: Additional arguments for the API

        Returns:
            List of embedding values

        Raises:
            ProviderAPIError: If the API call fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        if not self._client:
            raise ProviderInitError("OpenAI client not initialized")

        response: CreateEmbeddingResponse = await self._call_api(
            cast(
                ProviderCallback[CreateEmbeddingResponse],
                self._client.embeddings.create,
            ),
            input=text,
            model=EMBEDDING_MODEL,
            **kwargs,
        )

        if not response.data:
            return []
        return response.data[0].embedding

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the provider's model.

        Args:
            prompt: The prompt to complete
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text or async generator of text chunks if streaming

        Raises:
            ProviderError: If the API call fails or rate limit is exceeded
            RuntimeError: If provider is not initialized
        """
        message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": prompt,
        }
        return await self.chat(
            messages=[message],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs,
        )
