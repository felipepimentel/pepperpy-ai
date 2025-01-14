"""Test utilities."""

from collections.abc import AsyncGenerator
from typing import cast

from pepperpy.providers.base import BaseProvider
from pepperpy.providers.config import ProviderConfig
from pepperpy.responses import AIResponse, ResponseMetadata
from pepperpy.types import Message


class TestProvider(BaseProvider[ProviderConfig]):
    """Test provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._initialized: bool = False

    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider."""
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
        """
        yield AIResponse(
            content="Hello, how can I help you?",
            metadata=cast(ResponseMetadata, {"model": "test", "provider": "test"}),
        )
