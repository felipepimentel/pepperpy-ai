"""OpenRouter provider implementation."""

from collections.abc import AsyncGenerator
from typing import NotRequired, TypedDict, cast

from openrouter import AsyncOpenRouter

from ..ai_types import Message
from ..responses import AIResponse, ResponseMetadata
from .base import BaseProvider
from .exceptions import ProviderError


class OpenRouterConfig(TypedDict):
    """OpenRouter provider configuration."""

    model: str  # Required field
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]


class OpenRouterProvider(BaseProvider[OpenRouterConfig]):
    """OpenRouter provider implementation."""

    def __init__(self, config: OpenRouterConfig, api_key: str) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
            api_key: OpenRouter API key
        """
        super().__init__(config, api_key)
        self._client: AsyncOpenRouter | None = None

    @property
    def client(self) -> AsyncOpenRouter:
        """Get client instance.

        Returns:
            AsyncOpenRouter: Client instance.

        Raises:
            ProviderError: If provider is not initialized.
        """
        if not self.is_initialized or not self._client:
            raise ProviderError(
                "Provider not initialized",
                provider="openrouter",
                operation="get_client",
            )
        return self._client

    async def initialize(self) -> None:
        """Initialize provider."""
        if not self._initialized:
            self._client = AsyncOpenRouter(api_key=self.api_key)
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        if self._client:
            await self._client.close()
        self._initialized = False
        self._client = None

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from OpenRouter.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized or streaming fails
        """
        if not self.is_initialized:
            raise ProviderError(
                "Provider not initialized",
                provider="openrouter",
                operation="stream",
            )

        try:
            async with self.client.chat.completions.stream(
                messages=[
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ],
                model=model or self.config["model"],
                temperature=temperature or self.config.get("temperature", 0.7),
                max_tokens=max_tokens or self.config.get("max_tokens", 1000),
                stream=True,
            ) as stream:
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield AIResponse(
                            content=chunk.choices[0].delta.content,
                            metadata=cast(ResponseMetadata, {
                                "model": model or self.config["model"],
                                "provider": "openrouter",
                                "usage": {"total_tokens": 0},
                                "finish_reason": chunk.choices[0].finish_reason or None,
                            }),
                        )
        except Exception as e:
            raise ProviderError(
                "Failed to stream responses",
                provider="openrouter",
                operation="stream",
                cause=e,
            ) from e
