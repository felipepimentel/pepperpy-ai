"""Gemini provider implementation for the Pepperpy framework.

This module implements the Gemini provider, supporting text generation
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

from collections.abc import AsyncGenerator
from typing import Any, cast

import google.generativeai as genai
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types import GenerationConfig

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
    - Streaming responses
    - Rate limit handling
    - Proper error propagation

    Attributes:
        config (ProviderConfig): The provider configuration
        _client (Any): The Gemini client instance
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
        self._client: Any = None
        self._model = config.model or "gemini-pro"

    async def initialize(self) -> None:
        """Initialize the Gemini client.

        This method configures the Gemini API with the provided API key and
        initializes the generative model.

        Raises:
            ProviderInitError: If initialization fails
        """
        if not self.config.api_key:
            raise ProviderInitError(
                "API key is required",
                provider_type="gemini",
            )

        try:
            configure(api_key=self.config.api_key.get_secret_value())
            self._client = GenerativeModel(self._model)
            self._initialized = True  # Set initialized flag
            logger.info("Initialized Gemini provider", extra={"model": self._model})
        except Exception as e:
            raise ProviderInitError(
                f"Failed to initialize Gemini provider: {e}",
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
        """Complete a prompt using the Gemini API.

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
                "Gemini provider not initialized",
                provider_type="gemini",
            )

        try:
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                **kwargs,
            )

            if stream:

                async def response_generator() -> AsyncGenerator[str, None]:
                    response = await self._client.generate_content_async(
                        prompt,
                        generation_config=generation_config,
                        stream=True,
                    )
                    async for chunk in response:
                        yield cast(str, chunk.text)

                return response_generator()

            response = await self._client.generate_content_async(
                prompt,
                generation_config=generation_config,
                stream=False,
            )
            return cast(str, response.text)

        except Exception as e:
            if "quota" in str(e).lower():
                raise ProviderRateLimitError(
                    "Gemini rate limit exceeded",
                    provider_type="gemini",
                    details={"error": str(e)},
                ) from e
            raise ProviderAPIError(
                f"Gemini API error: {e}",
                provider_type="gemini",
                details={"error": str(e)},
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._client = None
        logger.info("Gemini provider cleaned up", extra={"model": self._model})

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for the given text.

        Args:
            text: Text to generate embeddings for
            **kwargs: Additional keyword arguments

        Returns:
            List of embedding values

        Raises:
            ProviderAPIError: If the API request fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        self._check_initialized()

        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        except Exception as e:
            if "quota exceeded" in str(e).lower():
                raise ProviderRateLimitError(
                    "Gemini rate limit exceeded",
                    provider_type="gemini",
                    details={"error": str(e)},
                ) from e
            raise ProviderAPIError(
                f"Gemini API error: {e}",
                provider_type="gemini",
                details={"error": str(e)},
            ) from e
