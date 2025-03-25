"""LLM component module."""

from typing import Any, List, Optional

from pepperpy.core.base import BaseComponent
from pepperpy.core.config import Config
from pepperpy.llm.base import LLMProvider, Message


class LLMComponent(BaseComponent):
    """LLM component for text generation."""

    def __init__(self, config: Config) -> None:
        """Initialize LLM component.

        Args:
            config: Configuration instance
        """
        super().__init__()
        self.config = config
        self._provider: Optional[LLMProvider] = None

    async def _initialize(self) -> None:
        """Initialize the LLM provider."""
        self._provider = self.config.load_llm_provider()
        await self._provider.initialize()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._provider:
            await self._provider.cleanup()

    async def generate(self, messages: List[Message]) -> Any:
        """Generate text from messages.

        Args:
            messages: List of messages

        Returns:
            Generated text
        """
        if not self._provider:
            await self.initialize()
        return await self._provider.generate(messages)
