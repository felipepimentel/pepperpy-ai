"""
Anthropic Claude provider implementation.
"""
import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

import anthropic
from anthropic import AsyncAnthropic

from pepperpy.core.utils.errors import ProviderError
from pepperpy.providers.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", **kwargs: Any) -> None:
        """Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key.
            model: Model name to use.
            **kwargs: Additional configuration parameters.
        """
        super().__init__({"api_key": api_key, "model": model, **kwargs})
        self._client: Optional[AsyncAnthropic] = None
        self._model = model

    async def initialize(self) -> None:
        """Initialize the Anthropic client.

        Raises:
            ProviderError: If initialization fails.
        """
        try:
            await self.validate_config()
            self._client = AsyncAnthropic(api_key=self.config["api_key"])
            self._initialized = True
        except Exception as e:
            raise ProviderError(f"Failed to initialize Anthropic provider: {str(e)}") from e

    async def validate_config(self) -> None:
        """Validate the provider configuration.

        Raises:
            ProviderError: If configuration is invalid.
        """
        if not self.config.get("api_key"):
            raise ProviderError("Anthropic API key is required")
        if not self.config.get("model"):
            raise ProviderError("Model name is required")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
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
        """Generate text using Anthropic Claude.

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
        if not self._client or not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            response = await self._client.messages.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop_sequences=stop,
                **kwargs,
            )
            return response.content[0].text
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
        """Generate text using Anthropic Claude in streaming mode.

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
        if not self._client or not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            stream = await self._client.messages.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop_sequences=stop,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.content:
                    yield chunk.content[0].text
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
        try:
            return anthropic.count_tokens(text)
        except Exception as e:
            raise ProviderError(f"Token counting failed: {str(e)}") from e

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.

        Returns:
            A dictionary containing model information.

        Raises:
            ProviderError: If retrieving model info fails.
        """
        if not self._client or not self._initialized:
            raise ProviderError("Provider not initialized")

        return {
            "name": self._model,
            "provider": "anthropic",
            "capabilities": {
                "streaming": True,
                "function_calling": True,
                "vision": True,
            },
        } 