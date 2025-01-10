"""AI client protocol definition."""

from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

from .ai_types import AIResponse
from .config import AIConfig


@runtime_checkable
class AIClient(Protocol):
    """AI client protocol."""

    @property
    def config(self) -> AIConfig:
        """Get client configuration."""
        ...

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        ...

    async def initialize(self) -> None:
        """Initialize client."""
        ...

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        ...

    async def complete(self, prompt: str) -> AIResponse:
        """Complete prompt."""
        ...

    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses."""
        ...

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding for text."""
        ...
