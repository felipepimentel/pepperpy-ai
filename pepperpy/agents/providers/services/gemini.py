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
from typing import cast

import google.generativeai as genai  # type: ignore[import]
from google.generativeai.client import configure  # type: ignore[import]
from google.generativeai.generative_models import (
    GenerativeModel,  # type: ignore[import]
)
from google.generativeai.types import GenerationConfig  # type: ignore[import]
from pydantic import Field

from pepperpy.monitoring.logger import structured_logger as logger

from ..base import (
    BaseProvider as Provider,
)
from ..base import (
    EmbeddingKwargs,
    ProviderConfig,
    ProviderKwargs,
)
from ..domain import (
    ProviderAPIError,
    ProviderInitError,
    ProviderRateLimitError,
)


class GeminiConfig(ProviderConfig):
    """Configuration for the Gemini provider.

    Attributes:
        model: Model to use (default: gemini-pro)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens per request (default: 2048)
        top_p: Top-p sampling parameter (default: 1.0)
        top_k: Top-k sampling parameter (default: 40)
    """

    model: str = Field(default="gemini-pro", description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens per request")
    top_p: float = Field(default=1.0, description="Top-p sampling parameter")
    top_k: int = Field(default=40, description="Top-k sampling parameter")


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
        _client (GenerativeModel): The Gemini client instance
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
        self._client: GenerativeModel | None = None
        self._model = config.model or "gemini-pro"
        self.config = cast(GeminiConfig, config)

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
            configure(api_key=self.config.api_key.get_secret_value())  # type: ignore[call-arg]
            self._client = GenerativeModel(self._model)
            self._initialized = True  # Set initialized flag
            logger.info("Initialized Gemini provider", model=self._model)
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
        **kwargs: ProviderKwargs,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a text prompt using the Gemini model.

        Args:
            prompt: The text prompt to complete
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: None)
            stream: Whether to stream the response (default: False)
            **kwargs: Additional keyword arguments passed to the model

        Returns:
            Either a string containing the complete response, or an async
            generator yielding response chunks if streaming is enabled.

        Raises:
            ProviderAPIError: If the API request fails
            ProviderRateLimitError: If rate limits are exceeded
            ProviderInitError: If the provider is not initialized
        """
        if not self._client:
            raise ProviderInitError(
                "Provider not initialized",
                provider_type="gemini",
            )

        client = self._client  # Type guard
        try:
            model_params = kwargs.get("model_params", {})
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=model_params.get("top_p", 1.0),
                top_k=model_params.get("top_k", 40),
            )

            if stream:

                async def response_generator() -> AsyncGenerator[str, None]:
                    response = await client.generate_content_async(  # type: ignore[call-arg]
                        prompt,
                        generation_config=generation_config,
                        stream=True,
                    )
                    async for chunk in response:
                        yield cast(str, chunk.text)

                return response_generator()

            response = await client.generate_content_async(  # type: ignore[call-arg]
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
        logger.info("Gemini provider cleaned up", model=self._model)

    async def embed(self, text: str, **kwargs: EmbeddingKwargs) -> list[float]:
        """Generate embeddings for text using Gemini.

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
            model_name = str(kwargs.get("model", "models/embedding-001"))
            result = genai.embed_content(  # type: ignore[attr-defined]
                model=model_name,  # type: ignore[arg-type]
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]  # type: ignore[index]
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
