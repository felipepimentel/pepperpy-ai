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
from typing import Any, Dict, Union, cast

import google.generativeai as genai  # type: ignore[import]
from google.generativeai.client import configure  # type: ignore[import]
from google.generativeai.generative_models import (
    GenerativeModel,  # type: ignore[import]
)
from google.generativeai.types import (
    AsyncGenerateContentResponse,  # type: ignore[import]
    GenerationConfig,  # type: ignore[import]
)
from pydantic import Field, SecretStr

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger
from pepperpy.core.messages import ProviderMessage, ProviderResponse
from pepperpy.core.providers.base import BaseProvider, ProviderConfig
from pepperpy.core.providers.errors import (
    ProviderError,
)
from pepperpy.core.providers.errors import (
    ProviderResourceError as ProviderInitError,
)
from pepperpy.core.providers.errors import (
    ProviderRuntimeError as ProviderAPIError,
)

# Configure logger
logger = get_logger(__name__)

# Type aliases for provider parameters
GenerateKwargs = Dict[str, Any]
StreamKwargs = Dict[str, Any]


class GeminiConfig(ProviderConfig):
    """Configuration for the Gemini provider.

    Attributes:
        api_key: Gemini API key
        model: Model to use (default: gemini-pro)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens per request (default: 2048)
        top_p: Top-p sampling parameter (default: 1.0)
        top_k: Top-k sampling parameter (default: 40)
    """

    api_key: SecretStr = Field(default=SecretStr(""), description="Gemini API key")
    model: str = Field(default="gemini-pro", description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens per request")
    top_p: float = Field(default=1.0, description="Top-p sampling parameter")
    top_k: int = Field(default=40, description="Top-k sampling parameter")

    class Config:
        extra = "forbid"


class GeminiProvider(BaseProvider):
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
        # Convert to GeminiConfig if needed
        gemini_config = (
            config
            if isinstance(config, GeminiConfig)
            else GeminiConfig(
                type="gemini",
                config={
                    **config.config,
                    "api_key": config.config.get("api_key", ""),
                },
            )
        )
        super().__init__(gemini_config)
        self._client: GenerativeModel | None = None
        self._model = gemini_config.model
        self._config = gemini_config

    async def initialize(self) -> None:
        """Initialize the Gemini client.

        This method configures the Gemini API with the provided API key and
        initializes the generative model.

        Raises:
            ProviderInitError: If initialization fails
        """
        if not self._config.api_key:
            raise ProviderInitError(
                "API key is required",
                provider_type="gemini",
            )

        try:
            configure(api_key=self._config.api_key.get_secret_value())  # type: ignore[call-arg]
            self._client = GenerativeModel(self._model)
            self._initialized = True  # Set initialized flag
            logger.info("Initialized Gemini provider", extra={"model": self._model})
        except Exception as e:
            raise ProviderInitError(
                f"Failed to initialize Gemini provider: {e}",
                provider_type="gemini",
                details={"error": str(e)},
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._client:
            try:
                self._client = None
                await super().cleanup()
                self._initialized = False
                logger.info("Gemini provider cleaned up", extra={"model": self._model})
            except Exception as exc:
                logger.error(f"Error during cleanup: {exc!r}")
                raise ProviderError(
                    message=f"Cleanup failed: {exc}",
                    provider_type="gemini",
                    details={"error": str(exc)},
                ) from exc

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
            ConfigurationError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ConfigurationError("Provider not initialized")

        try:
            if not self._client:
                raise ProviderError("Gemini client not initialized")

            # Get generation parameters
            temperature = message.metadata.get("temperature", self._config.temperature)
            max_tokens = message.metadata.get("max_tokens", self._config.max_tokens)
            stream = message.metadata.get("stream", False)
            top_p = message.metadata.get("top_p", self._config.top_p)
            top_k = message.metadata.get("top_k", self._config.top_k)

            # Configure generation
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
            )

            # Generate response
            if stream:
                response = await self._client.generate_content_async(  # type: ignore[call-arg]
                    str(message.content),
                    generation_config=generation_config,
                    stream=True,
                )
                return self._stream_response(response)
            else:
                response = await self._client.generate_content_async(  # type: ignore[call-arg]
                    str(message.content),
                    generation_config=generation_config,
                    stream=False,
                )
                return ProviderResponse(
                    content=cast(str, response.text),
                    metadata={
                        "model": self._model,
                        "finish_reason": response.prompt_feedback.block_reason
                        or "stop",
                    },
                )

        except Exception as e:
            if "quota" in str(e).lower():
                raise ProviderAPIError(
                    "Gemini rate limit exceeded",
                    provider_type="gemini",
                    details={"error": str(e)},
                ) from e
            raise ProviderError(
                message=f"Gemini API error: {e}",
                provider_type="gemini",
                details={"error": str(e)},
            ) from e

    async def _stream_response(
        self, response: AsyncGenerateContentResponse
    ) -> AsyncGenerator[ProviderResponse, None]:
        """Stream response chunks.

        Args:
            response: Gemini response stream

        Yields:
            Provider response chunks
        """
        async for chunk in response:
            if chunk.text:
                yield ProviderResponse(
                    content=cast(str, chunk.text),
                    metadata={
                        "model": self._model,
                        "finish_reason": chunk.prompt_feedback.block_reason or "stop",
                    },
                )

    async def embed(
        self,
        text: str,
        *,
        model: str | None = None,
        **kwargs: Any,
    ) -> list[float]:
        """Generate embeddings for the given text.

        Args:
            text: Text to generate embeddings for
            model: Model to use for embeddings
            **kwargs: Additional keyword arguments

        Returns:
            List of embeddings

        Raises:
            ProviderError: If embedding generation fails
            ConfigurationError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ConfigurationError("Provider not initialized")

        try:
            model_name = model or "models/embedding-001"
            result = genai.embed_content(  # type: ignore[attr-defined]
                model=model_name,  # type: ignore[arg-type]
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]  # type: ignore[index]
        except Exception as e:
            if "quota exceeded" in str(e).lower():
                raise ProviderAPIError(
                    "Gemini rate limit exceeded",
                    provider_type="gemini",
                    details={"error": str(e)},
                ) from e
            raise ProviderError(
                message=f"Gemini API error: {e}",
                provider_type="gemini",
                details={"error": str(e)},
            ) from e
