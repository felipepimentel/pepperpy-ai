"""Mock provider for testing."""

from typing import AsyncIterator

from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse


class MockProvider(BaseProvider):
    """Mock provider for testing."""

    async def complete(self, prompt: str) -> AIResponse:
        """Return a mock completion response."""
        return AIResponse(content="Mock completion")

    async def stream(self, prompt: str) -> AsyncIterator[AIResponse]:
        """Return a mock stream response."""
        async def mock_stream() -> AsyncIterator[AIResponse]:
            yield AIResponse(content="Mock stream")
        return mock_stream() 