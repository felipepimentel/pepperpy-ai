"""Mock provider for testing."""

from typing import Any

from pepperpy_ai.responses import AIResponse
from pepperpy_ai.providers.base import BaseProvider


class MockProvider(BaseProvider):
    """Mock provider for testing."""
    
    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Mock completion method."""
        return AIResponse(content="Mock completion")
    
    async def stream(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Mock streaming method."""
        return AIResponse(content="Mock stream") 