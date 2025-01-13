"""Anthropic provider implementation."""

import importlib.util
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from ..exceptions import DependencyError
from ..responses import AIResponse
from ..types import Message
from .base import BaseProvider
from .config import ProviderConfig
from .exceptions import ProviderError

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic


def _check_anthropic_dependency() -> None:
    """Check if Anthropic package is installed."""
    if importlib.util.find_spec("anthropic") is None:
        raise DependencyError(
            feature="Anthropic provider",
            package="anthropic",
            extra="anthropic",
        )


class AnthropicProvider(BaseProvider[ProviderConfig]):
    """Anthropic provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration

        Raises:
            DependencyError: If Anthropic package is not installed
        """
        _check_anthropic_dependency()
        super().__init__(config, api_key=config.get("api_key", ""))
        self._client: AsyncAnthropic | None = None
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized

    @property
    def client(self) -> "AsyncAnthropic":
        """Get client instance."""
        if not self._client:
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def initialize(self) -> None:
        """Initialize provider resources."""
        if not self._initialized:
            _check_anthropic_dependency()
            import anthropic

            timeout = float(self.config.get("timeout", 30.0))
            self._client = anthropic.AsyncAnthropic(
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
            raise ProviderError("Provider is not initialized")

        try:
            stream = await self.client.messages.stream(
                messages=[
                    {"role": msg.role.value.lower(), "content": msg.content}
                    for msg in messages
                ],
                model=str(model or self.config.get("model")),
                temperature=float(temperature or self.config.get("temperature", 0.7)),
                max_tokens=int(max_tokens or self.config.get("max_tokens", 1000)),
            )

            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield AIResponse(
                        content=chunk.content[0].text,
                        metadata={
                            "model": str(model or self.config.get("model")),
                            "provider": "anthropic",
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0,
                            },
                            "finish_reason": chunk.type
                            if hasattr(chunk, "type")
                            else None,
                        },
                    )
        except Exception as e:
            raise ProviderError(f"Failed to stream responses: {e}") from e
