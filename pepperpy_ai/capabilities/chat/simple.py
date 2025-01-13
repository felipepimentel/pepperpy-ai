"""Simple chat capability implementation."""

from collections.abc import AsyncGenerator
from typing import Any, Generic, TypeVar

from ...providers.base import BaseProvider
from ...responses import AIResponse
from ...types import Message
from ..base import BaseCapability
from .config import ChatConfig

TProvider = TypeVar("TProvider", bound=BaseProvider[Any])


class SimpleChatCapability(BaseCapability[ChatConfig], Generic[TProvider]):
    """Simple chat capability implementation."""

    def __init__(self, config: ChatConfig, provider: type[TProvider]) -> None:
        """Initialize simple chat capability.

        Args:
            config: Chat configuration
            provider: Provider class to use
        """
        super().__init__(config)
        self._provider = provider(config)

    async def initialize(self) -> None:
        """Initialize capability."""
        await self._provider.initialize()

    async def cleanup(self) -> None:
        """Cleanup capability."""
        await self._provider.cleanup()

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the capability.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional capability-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        stream = await self._provider.stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        async for response in stream:
            yield response
