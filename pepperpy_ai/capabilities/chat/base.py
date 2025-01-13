"""Base chat capability module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TypedDict

from ...responses import AIResponse
from ...types import Message


class ChatKwargs(TypedDict, total=False):
    """Chat keyword arguments."""

    model: str
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    timeout: float


class BaseChatCapability(ABC):
    """Base chat capability."""

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: ChatKwargs,
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
