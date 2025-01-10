"""LLM client implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from ..ai_types import AIResponse
from .config import LLMConfig


class LLMClient(ABC):
    """Base LLM client."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize client."""
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize client."""
        await self._setup()
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        await self._teardown()
        self._initialized = False

    @abstractmethod
    async def _setup(self) -> None:
        """Setup client resources."""
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown client resources."""
        pass

    @abstractmethod
    async def complete(self, prompt: str) -> AIResponse:
        """Complete prompt."""
        pass

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses."""
        pass
