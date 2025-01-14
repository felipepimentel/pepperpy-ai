"""Base provider module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Coroutine
from typing import Any, Generic, TypeVar

from ..responses import AIResponse
from ..types import Message
from .config import ProviderConfig

TConfig = TypeVar("TConfig", bound=ProviderConfig)


class BaseProvider(ABC, Generic[TConfig]):
    """Base provider class."""

    def __init__(self, config: TConfig) -> None:
        """Initialize base provider.

        Args:
            config: The provider configuration.
        """
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup provider."""
        raise NotImplementedError

    @abstractmethod
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
            messages: The list of messages to process.
            model: The model to use for the chat.
            temperature: The temperature to use for the chat.
            max_tokens: The maximum number of tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Returns:
            An async generator yielding responses.

        Raises:
            ValueError: If no messages are provided or if the last message is not
                from the user.
        """
        raise NotImplementedError
