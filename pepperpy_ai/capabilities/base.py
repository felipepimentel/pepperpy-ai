"""Base capability module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Coroutine
from typing import Any, Generic, TypeVar

from ..config.capability import CapabilityConfig
from ..responses import AIResponse
from ..types import Message

TConfig = TypeVar("TConfig", bound=CapabilityConfig)


class BaseCapability(ABC, Generic[TConfig]):
    """Base capability class."""

    def __init__(self, config: TConfig) -> None:
        """Initialize base capability.

        Args:
            config: The capability configuration.
        """
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the capability is initialized."""
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize capability."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup capability."""
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
        """Stream responses from the capability.

        Args:
            messages: The list of messages to process.
            model: The model to use for the chat.
            temperature: The temperature to use for the chat.
            max_tokens: The maximum number of tokens to generate.
            **kwargs: Additional capability-specific parameters.

        Returns:
            An async generator yielding responses.

        Raises:
            ValueError: If no messages are provided or if the last message is not
                from the user.
        """
        raise NotImplementedError
