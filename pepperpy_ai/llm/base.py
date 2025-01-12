"""Base LLM client implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import List, Optional

from ..ai_types import Message
from ..responses import AIResponse
from ..exceptions import ProviderError
from ..providers.base import BaseProvider
from .config import LLMConfig


class LLMClient(BaseProvider[LLMConfig], ABC):
    """Base LLM client implementation."""

    async def initialize(self) -> None:
        """Initialize provider."""
        await self._setup()
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        await self._teardown()
        self._initialized = False

    async def _setup(self) -> None:
        """Setup client resources."""
        pass

    async def _teardown(self) -> None:
        """Teardown client resources."""
        pass

    @abstractmethod
    async def complete(self, prompt: str) -> AIResponse:
        """Complete prompt.

        Args:
            prompt: The prompt to complete

        Returns:
            AIResponse: The completion response
        """
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to send to the provider
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError("Provider not initialized", provider="llm")
        yield AIResponse(content="Not implemented", provider="llm")
