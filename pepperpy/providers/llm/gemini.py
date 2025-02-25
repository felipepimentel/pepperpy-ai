"""Google Gemini provider module.

This module implements the Google Gemini provider for LLM functionality.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any, Optional

import google.generativeai as genai
from pydantic import Field

from pepperpy.core.providers.unified import ProviderConfig
from pepperpy.providers.llm.base import LLMMessage, LLMProvider, LLMResponse
from pepperpy.core.providers.errors import (
    ProviderResourceError as ProviderInitError,
)
from pepperpy.core.providers.errors import (
    ProviderRuntimeError as ProviderAPIError,
)

# Configure logger
logger = get_logger(__name__)

# Type aliases for provider parameters
GenerateKwargs = dict[str, Any]
StreamKwargs = dict[str, Any]


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
class GeminiConfig(ProviderConfig):
    """Configuration for Gemini provider."""

    api_key: str = Field(description="Google API key")
    model: str = Field(default="gemini-pro", description="Model name to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(default=None, description="Nucleus sampling parameter")
    top_k: Optional[int] = Field(default=None, description="Top-k sampling parameter")

class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""

    config_class = GeminiConfig

    def __init__(self, config: GeminiConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(config.model)

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
        response = await self.model.generate_content_async(
            message.content,
            generation_config={
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
            },
            stream=True,
        )

        async def stream_response() -> AsyncGenerator[LLMResponse, None]:
            async for chunk in response:
                yield LLMResponse(
                    content=chunk.text,
                    model=self.config.model,
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    finish_reason=None,
                )

        return stream_response()

    async def embed(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
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

        Raises:
            NotImplementedError: Embeddings not supported by Gemini
        """
        raise NotImplementedError("Embeddings not supported by Gemini")

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
        # Combine messages into a single prompt
        prompt = "\n".join(f"{msg.role}: {msg.content}" for msg in messages)

        response = await self.model.generate_content_async(
            prompt,
            generation_config={
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
            },
        )

        return LLMResponse(
            content=response.text,
            model=self.config.model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="stop",
        )
