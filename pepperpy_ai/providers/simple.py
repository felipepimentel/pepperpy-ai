"""Simple provider implementation."""

from collections.abc import AsyncGenerator

from ..responses import AIResponse
from ..types import Message
from .base import BaseProvider
from .config import ProviderConfig
from .exceptions import ProviderError


class SimpleProvider(BaseProvider[ProviderConfig]):
    """Simple provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize simple provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider resources."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        self._initialized = False

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized or streaming fails
        """
        if not self.is_initialized:
            raise ProviderError("Provider is not initialized")

        try:
            yield AIResponse(
                content="Hello, how can I help you?",
                metadata={
                    "model": model or "simple",
                    "provider": "simple",
                    "finish_reason": "stop",
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                },
            )
        except Exception as e:
            raise ProviderError(f"Failed to stream responses: {e}") from e
