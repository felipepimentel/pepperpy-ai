"""Base provider module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Generic, TypeVar

from ..ai_types import Message
from ..responses import AIResponse
from .exceptions import ProviderError

TConfig = TypeVar("TConfig")


class BaseProvider(Generic[TConfig], ABC):
    """Base class for all AI providers."""

    def __init__(self, config: TConfig, api_key: str) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
            api_key: API key for provider
        """
        self.config = config
        self.api_key = api_key
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup provider resources."""
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
            messages: List of messages to send to the provider
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError(
                "Provider not initialized",
                provider="base",
                operation="stream",
            )
        yield AIResponse(
            content="Not implemented",
            metadata={
                "provider": "base",
                "model": "base",
                "usage": {"total_tokens": 0}
            },
        )
