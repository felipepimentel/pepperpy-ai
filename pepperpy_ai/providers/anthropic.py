"""Anthropic provider implementation."""

from collections.abc import AsyncGenerator
from typing import Any

from ..ai_types import AIResponse
from ..llm.base import LLMClient
from ..llm.config import LLMConfig


class AnthropicProvider(LLMClient):
    """Anthropic provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize provider."""
        super().__init__(config)
        self._client: Any = None

    async def _setup(self) -> None:
        """Setup provider resources."""
        # Implementação específica do Anthropic
        pass

    async def _teardown(self) -> None:
        """Teardown provider resources."""
        self._client = None

    async def complete(self, prompt: str) -> AIResponse:
        """Complete prompt."""
        raise NotImplementedError

    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses."""
        raise NotImplementedError
