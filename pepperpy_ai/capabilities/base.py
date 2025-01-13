"""Base capability implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Generic, TypeVar

from ..responses import AIResponse
from ..types import Message
from .config import CapabilityConfig

T = TypeVar("T", bound=CapabilityConfig)


class BaseCapability(ABC, Generic[T]):
    """Base capability implementation."""

    def __init__(self, config: T) -> None:
        """Initialize base capability.

        Args:
            config: Capability configuration
        """
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize capability."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup capability."""
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the capability.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        raise NotImplementedError
