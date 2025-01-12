"""Mock provider module."""

from collections.abc import AsyncGenerator
from typing import List, Optional
import asyncio

from ..ai_types import Message
from ..exceptions import ProviderError
from ..responses import AIResponse
from .base import BaseProvider
from .config import ProviderConfig


class MockProvider(BaseProvider[ProviderConfig]):
    """Mock provider implementation."""

    def __init__(self, config: ProviderConfig, api_key: str) -> None:
        """Initialize mock provider.

        Args:
            config: Provider configuration
            api_key: API key for provider
        """
        super().__init__(config, api_key)
        self._mock_response = "This is a mock response that will be streamed character by character."

    async def initialize(self) -> None:
        """Initialize mock provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup mock provider."""
        self._initialized = False

    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream mock responses.

        Args:
            messages: List of messages to process
            model: Model to use for completion (ignored)
            temperature: Temperature to use for completion (ignored)
            max_tokens: Maximum number of tokens to generate (ignored)

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError("Provider not initialized", provider="mock")

        try:
            # Simulate streaming response
            response = "This is a mock response."
            for word in response.split():
                yield AIResponse(
                    content=word + " ",
                    model="mock-model",
                    provider="mock"
                )
                await asyncio.sleep(0.1)  # Simulate delay
        except Exception as e:
            raise ProviderError(f"Mock streaming error: {str(e)}", provider="mock")
