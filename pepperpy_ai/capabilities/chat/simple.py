"""Simple chat capability module."""

from collections.abc import AsyncGenerator, Coroutine
from typing import Any

from ...responses import AIResponse
from ...types import Message
from ..base import BaseCapability


class SimpleChatCapability(BaseCapability):
    """Simple chat capability."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the capability.

        Args:
            config: The capability configuration.
        """
        super().__init__(config)
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the capability is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the capability."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up the capability."""
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
        """Stream responses from the capability.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional capability-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            NotImplementedError: This capability does not support streaming.
        """
        raise NotImplementedError("SimpleChatCapability does not support streaming")
