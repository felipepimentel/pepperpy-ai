"""Base provider implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Generic, Protocol, TypeVar

from ..ai_types import AIResponse
from .config import ProviderConfig

ConfigT = TypeVar("ConfigT", bound=ProviderConfig)


class BaseProvider(Generic[ConfigT], ABC):
    """Base provider implementation."""

    def __init__(self, config: ConfigT) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider."""
        if not self._initialized:
            await self._setup()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        if self._initialized:
            await self._teardown()
            self._initialized = False

    @abstractmethod
    async def _setup(self) -> None:
        """Setup provider resources."""
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown provider resources."""
        pass

    @abstractmethod
    async def complete(self, prompt: str) -> AIResponse:
        """Complete prompt."""
        pass

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses."""
        pass


class AIProvider(Protocol):
    """Protocol for AI providers."""

    async def generate_response(
        self,
        *,  # Force keyword arguments
        prompt: str,
        system_message: str | None = None,
        conversation_history: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Generate a response from the AI provider.

        Args:
            prompt: The prompt to send
            system_message: Optional system message
            conversation_history: Optional conversation history
            metadata: Optional metadata

        Returns:
            The generated response
        """
        ...
