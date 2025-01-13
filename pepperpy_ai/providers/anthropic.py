"""Anthropic provider implementation."""

import importlib.util
from collections.abc import AsyncGenerator
from typing import Any, NotRequired, TypedDict, cast

from ..ai_types import Message
from ..exceptions import DependencyError
from ..responses import AIResponse, ResponseMetadata
from .base import BaseProvider
from .exceptions import ProviderError


def _check_anthropic_dependency() -> None:
    """Check if Anthropic package is installed.

    Raises:
        DependencyError: If Anthropic package is not installed.
    """
    if importlib.util.find_spec("anthropic") is None:
        raise DependencyError(
            feature="Anthropic provider",
            package="anthropic",
            extra="anthropic",
        )


class AnthropicConfig(TypedDict):
    """Anthropic provider configuration."""

    model: str  # Required field
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    top_k: NotRequired[int]
    timeout: NotRequired[float]


class AnthropicProvider(BaseProvider[AnthropicConfig]):
    """Anthropic provider implementation."""

    def __init__(self, config: AnthropicConfig, api_key: str) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
            api_key: Anthropic API key

        Raises:
            DependencyError: If Anthropic package is not installed
        """
        _check_anthropic_dependency()
        super().__init__(config, api_key)
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Get client instance.

        Returns:
            AsyncAnthropic: Client instance.

        Raises:
            ProviderError: If provider is not initialized.
        """
        if not self.is_initialized or not self._client:
            raise ProviderError(
                "Provider not initialized",
                provider="anthropic",
                operation="get_client",
            )
        return self._client

    async def initialize(self) -> None:
        """Initialize provider."""
        if not self._initialized:
            _check_anthropic_dependency()
            from anthropic import AsyncAnthropic

            timeout = self.config.get("timeout", 30.0)
            self._client = AsyncAnthropic(
                api_key=self.api_key,
                timeout=timeout,
            )
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
        """Stream responses from Anthropic.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized or streaming fails
            DependencyError: If Anthropic package is not installed
        """
        if not self.is_initialized:
            raise ProviderError(
                "Provider not initialized",
                provider="anthropic",
                operation="stream",
            )

        try:
            stream = await self.client.messages.stream(
                messages=[
                    {"role": msg.role.value.lower(), "content": msg.content}
                    for msg in messages
                ],
                model=model or self.config["model"],
                temperature=temperature or self.config.get("temperature", 0.7),
                max_tokens=max_tokens or self.config.get("max_tokens", 1000),
            )

            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield AIResponse(
                        content=chunk.content[0].text,
                        metadata=cast(ResponseMetadata, {
                            "model": model or self.config["model"],
                            "provider": "anthropic",
                            "usage": {"total_tokens": 0},
                            "finish_reason": chunk.type if hasattr(chunk, "type") else None,
                        }),
                    )
        except Exception as e:
            raise ProviderError(
                f"Failed to stream responses: {e!s}",
                provider="anthropic",
                operation="stream",
                cause=e,
            ) from e
