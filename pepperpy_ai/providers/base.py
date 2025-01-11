"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from pepperpy_ai.responses import AIResponse


class BaseProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    async def complete(self, prompt: str) -> AIResponse:
        """Complete a prompt with an AI response."""
        pass

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncIterator[AIResponse]:
        """Stream an AI response for a prompt."""
        pass
