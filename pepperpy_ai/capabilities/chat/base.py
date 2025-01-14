"""Base chat capability module."""

from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from ...responses import AIResponse
from ...types import Message
from ..base import BaseCapability


class BaseChatCapability(BaseCapability):
    """Base chat capability."""

    @abstractmethod
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
            **kwargs: Additional provider-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        raise NotImplementedError
