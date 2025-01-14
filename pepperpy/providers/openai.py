"""OpenAI provider module."""

from collections.abc import AsyncGenerator, Coroutine
from typing import Any

from ..responses import AIResponse
from ..types import Message
from .base import BaseProvider
from .config import ProviderConfig


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration.
        """
        super().__init__(config)
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up provider."""
        self._initialized = False

    def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Coroutine[Any, Any, AsyncGenerator[AIResponse, None]]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            NotImplementedError: This provider does not support streaming.
        """
        raise NotImplementedError("OpenAIProvider does not support streaming")
