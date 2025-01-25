"""
Google Gemini provider implementation.
"""
from typing import Any, AsyncIterator, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import AsyncGenerateContentResponse

from pepperpy.core.utils.errors import ProviderError
from pepperpy.providers.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""

    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs: Any) -> None:
        """Initialize the Gemini provider.

        Args:
            api_key: Google API key.
            model: Model name to use.
            **kwargs: Additional configuration parameters.
        """
        super().__init__({"api_key": api_key, "model": model, **kwargs})
        self._model = None
        self._model_name = model

    async def initialize(self) -> None:
        """Initialize the Gemini client.

        Raises:
            ProviderError: If initialization fails.
        """
        try:
            await self.validate_config()
            genai.configure(api_key=self.config["api_key"])
            self._model = genai.GenerativeModel(self._model_name)
            self._initialized = True
        except Exception as e:
            raise ProviderError(f"Failed to initialize Gemini provider: {str(e)}") from e

    async def validate_config(self) -> None:
        """Validate the provider configuration.

        Raises:
            ProviderError: If configuration is invalid.
        """
        if not self.config.get("api_key"):
            raise ProviderError("Google API key is required")
        if not self.config.get("model"):
            raise ProviderError("Model name is required")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        self._model = None
        self._initialized = False

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Google Gemini.

        Args:
            prompt: The input prompt.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature (0.0 to 1.0).
            top_p: Nucleus sampling parameter (0.0 to 1.0).
            stop: Optional list of stop sequences.
            **kwargs: Additional provider-specific parameters.

        Returns:
            The generated text.

        Raises:
            ProviderError: If generation fails.
        """
        if not self._model or not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": max_tokens,
                "stop_sequences": stop,
                **kwargs,
            }

            response = await self._model.generate_content_async(
                prompt,
                generation_config=generation_config,
            )
            return response.text
        except Exception as e:
            raise ProviderError(f"Text generation failed: {str(e)}") from e

    async def generate_stream(
        self,
        prompt: str,
        *,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate text using Google Gemini in streaming mode.

        Args:
            prompt: The input prompt.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature (0.0 to 1.0).
            top_p: Nucleus sampling parameter (0.0 to 1.0).
            stop: Optional list of stop sequences.
            **kwargs: Additional provider-specific parameters.

        Yields:
            Generated text chunks.

        Raises:
            ProviderError: If generation fails.
        """
        if not self._model or not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": max_tokens,
                "stop_sequences": stop,
                **kwargs,
            }

            stream = await self._model.generate_content_async(
                prompt,
                generation_config=generation_config,
                stream=True,
            )

            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise ProviderError(f"Streaming text generation failed: {str(e)}") from e

    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text.

        Args:
            text: The input text.

        Returns:
            The number of tokens.

        Raises:
            ProviderError: If token counting fails.
        """
        if not self._model or not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            return self._model.count_tokens(text).total_tokens
        except Exception as e:
            raise ProviderError(f"Token counting failed: {str(e)}") from e

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.

        Returns:
            A dictionary containing model information.

        Raises:
            ProviderError: If retrieving model info fails.
        """
        if not self._model or not self._initialized:
            raise ProviderError("Provider not initialized")

        return {
            "name": self._model_name,
            "provider": "google",
            "capabilities": {
                "streaming": True,
                "function_calling": True,
                "vision": self._model_name == "gemini-pro-vision",
            },
        } 