"""Mock provider implementation."""

from collections.abc import AsyncGenerator

from ..responses import AIResponse
from ..types import Message
from .base import BaseProvider, ProviderConfig
from .exceptions import ProviderError


class MockProvider(BaseProvider[ProviderConfig]):
    """Mock provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize mock provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized.

        Returns:
            True if provider is initialized, False otherwise
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider resources."""
        if not self._initialized:
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        if self._initialized:
            self._initialized = False

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream mock responses.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError(
                "Provider not initialized",
                provider="mock",
                operation="stream",
            )

        yield AIResponse(
            content="Mock response",
            metadata={
                "model": model or self.config.get("model", "mock"),
                "provider": "mock",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "finish_reason": "stop",
            },
        )
