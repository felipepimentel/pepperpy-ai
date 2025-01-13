"""Base provider implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Generic, TypeVar

from ..responses import AIResponse
from ..types import Message
from .config import ProviderConfig

T = TypeVar("T", bound=ProviderConfig)


class BaseProvider(ABC, Generic[T]):
    """Base provider implementation."""

    def __init__(self, config: T, api_key: str) -> None:
        """Initialize base provider.

        Args:
            config: Provider configuration
            api_key: API key for the provider
        """
        self.config = config
        self.api_key = api_key

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup provider."""
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
        """Stream responses from the provider.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        raise NotImplementedError
