"""Base LLM client implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from ..ai_types import AIResponse
from ..providers.base import BaseProvider
from .config import LLMConfig


class LLMClient(BaseProvider[LLMConfig], ABC):
    """Base LLM client implementation."""

    async def _setup(self) -> None:
        """Setup client resources."""
        pass

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
