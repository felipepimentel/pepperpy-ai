"""Gemini provider implementation for the Pepperpy framework.

This module implements the Gemini provider, supporting text generation and embeddings
using Google's Generative AI API. It handles streaming responses, rate limiting, and
proper error propagation.

Example:
    ```python
    config = ProviderConfig(
        provider_type="gemini",
        api_key="your-api-key"
    )
    provider = GeminiProvider(config)
    await provider.initialize()
    response = await provider.complete("Hello, how are you?")
    print(response)
    ```
"""

from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, Optional, Union, cast

import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import GenerationConfig
from google.generativeai.client import configure
from google.generativeai.embedding import embed_content
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types import AsyncGenerateContentResponse

from pepperpy.monitoring import logger

from ..domain import (
    ProviderAPIError,
    ProviderInitError,
    ProviderRateLimitError,
)
from ..provider import Provider, ProviderConfig


class GeminiProvider(Provider):
    """Provider implementation for Google's Gemini API.

    This provider implements the Provider protocol for Google's Generative AI API,
    supporting:
    - Text generation with Gemini Pro
    - Text embeddings with the embedding model
    - Streaming responses
    - Rate limit handling
    - Proper error propagation

    Attributes:
        config (ProviderConfig): The provider configuration
        _client (GenerativeModel | None): The Gemini client instance
        _model (str): The model to use for generation
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the Gemini provider.

        Args:
            config: Provider configuration containing API key and other settings

        Note:
            The provider is not ready for use until initialize() is called
        """
        super().__init__(config)
        self._model: str = config.model or "gemini-pro"
        self._client: GenerativeModel | None = None

    async def initialize(self) -> None:
        """Initialize the Gemini client.

        This method configures the Gemini API with the provided API key and
        initializes the generative model.

        Raises:
            ProviderInitError: If initialization fails
        """
        try:
            configure(api_key=self.config.api_key.get_secret_value())
            self._client = GenerativeModel(self._model)
            logger.info("Gemini provider initialized", model=self._model)
        except Exception as e:
            raise ProviderInitError(
                f"Failed to initialize Gemini provider: {e!s}",
                provider_type="gemini",
                details={"error": str(e)},
            ) from e

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the Gemini model.

        Args:
            prompt: The prompt to complete
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text or async generator of text chunks if streaming

        Raises:
            ProviderError: If the API call fails
        """
        if not self._client:
            raise ProviderInitError(
                "Gemini provider not initialized", provider_type="gemini"
            )

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens if max_tokens is not None else None,
            **kwargs,
        )

        try:
            if stream:
                response = await self._client.generate_content_async(
                    prompt,
                    generation_config=generation_config,
                    stream=True,
                )

                async def response_generator() -> AsyncGenerator[str, None]:
                    async for chunk in response:
                        if chunk.text:
                            yield chunk.text

                return response_generator()

            response = await self._client.generate_content_async(
                prompt,
                generation_config=generation_config,
                stream=False,
            )
            content: str = response.text
            return content

        except Exception as e:
            if "quota" in str(e).lower():
                raise ProviderRateLimitError(
                    "Gemini rate limit exceeded",
                    provider_type="gemini",
                    details={"error": str(e)},
                ) from e
            raise ProviderAPIError(
                f"Gemini API error: {e!s}",
                provider_type="gemini",
                details={"error": str(e)},
            ) from e

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text using Gemini.

        Args:
            text: Text to generate embeddings for
            **kwargs: Additional provider-specific parameters

        Returns:
            List of floating point values representing the text embedding

        Raises:
            ProviderAPIError: If the embedding generation fails
            ProviderInitError: If the client is not initialized

        Example:
            ```python
            # Generate embeddings
            embedding = await provider.embed("Hello world")
            print(f"Embedding dimension: {len(embedding)}")
            ```
        """
        if not self._client:
            raise ProviderInitError(
                "Gemini provider not initialized", provider_type="gemini"
            )

        try:
            result = embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document",
                title="text_embedding",
            )
            embeddings: list[float] = result["embedding"]
            return embeddings

        except Exception as e:
            raise ProviderAPIError(
                f"Gemini embedding error: {e!s}",
                provider_type="gemini",
                details={"error": str(e)},
            ) from e

    async def _stream_response(
        self,
        prompt: str,
        generation_config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """Stream response from Gemini.

        Args:
            prompt: The prompt to complete
            generation_config: Generation configuration

        Yields:
            Text chunks as they are generated by the model

        Raises:
            ProviderInitError: If client is not initialized
            ProviderAPIError: If streaming fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        if not self._client:
            raise ProviderInitError(
                "Gemini provider not initialized", provider_type="gemini"
            )

        response = await self._client.generate_content_async(
            prompt, generation_config=generation_config, stream=True
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method ensures proper cleanup of the Gemini provider resources.
        Currently, this is a no-op as the Gemini client doesn't require cleanup.
        """
        self._client = None
        logger.info("Gemini provider cleaned up", model=self._model)
