"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import Any

from pepperpy_ai.responses import AIResponse


class BaseProvider(ABC):
    """Base provider interface."""
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Complete a prompt."""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Stream responses for a prompt."""
        pass
