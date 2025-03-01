"""Perplexity AI provider module.

This module implements the Perplexity AI provider for LLM functionality.
"""

from collections.abc import AsyncGenerator
from typing import Any, List, Optional, Union

import httpx
from pydantic import Field

from pepperpy.core.common.providers.unified import ProviderConfig
from pepperpy.llm.base import LLMMessage, LLMProvider, LLMResponse


class PerplexityConfig(ProviderConfig):
    """Configuration for Perplexity provider."""

    api_key: str = Field(description="Perplexity API key")
    model: str = Field(default="pplx-7b-chat", description="Model name to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens to generate"
    )
    top_p: Optional[float] = Field(
        default=None, description="Nucleus sampling parameter"
    )
    top_k: Optional[int] = Field(default=None, description="Top-k sampling parameter")


class PerplexityProvider(LLMProvider):
    """Perplexity AI provider implementation."""

    config_class = PerplexityConfig

    def __init__(self, config: PerplexityConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.client = httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={"Authorization": f"Bearer {config.api_key}"},
        )

    async def process_message(
        self,
        message: LLMMessage,
    ) -> Union[LLMResponse, AsyncGenerator[LLMResponse, None]]:
        """Process a provider message.

        Args:
            message: Provider message

        Returns:
            Provider response or async generator of responses
        """
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.config.model,
                "messages": [{"role": message.role, "content": message.content}],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "stream": True,
            },
            timeout=None,
        )
        response.raise_for_status()

        async def stream_response() -> AsyncGenerator[LLMResponse, None]:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    chunk = httpx.json.loads(data)
                    if chunk.get("choices"):
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield LLMResponse(
                                content=content,
                                model=self.config.model,
                                usage={
                                    "prompt_tokens": 0,
                                    "completion_tokens": 0,
                                    "total_tokens": 0,
                                },
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
    ) -> List[float]:
        """Generate embeddings for text.

        Args:
            text: Input text
            model: Model to use for embeddings
            dimensions: Number of dimensions for embeddings
            **kwargs: Additional provider-specific arguments

        Returns:
            Text embeddings

        Raises:
            NotImplementedError: Embeddings not supported by Perplexity
        """
        raise NotImplementedError("Embeddings not supported by Perplexity")

    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response from messages.

        Args:
            messages: Input messages
            **kwargs: Additional provider-specific arguments

        Returns:
            Generated response
        """
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.config.model,
                "messages": [
                    {"role": msg.role, "content": msg.content} for msg in messages
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "stream": False,
            },
            timeout=None,
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=self.config.model,
            usage=data["usage"],
            finish_reason=data["choices"][0]["finish_reason"],
        )
