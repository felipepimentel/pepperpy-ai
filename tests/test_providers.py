"""Test provider functionality."""

from collections.abc import AsyncGenerator
from typing import NotRequired, TypedDict, cast

from pepperpy_ai.ai_types import Message
from pepperpy_ai.exceptions import ProviderError
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse, ResponseMetadata


class TestConfig(TypedDict):
    """Test provider configuration."""

    model: str  # Required field
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]


class TestProvider(BaseProvider[TestConfig]):
    """Test provider implementation."""

    def __init__(self, config: TestConfig, api_key: str) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
            api_key: Test API key
        """
        super().__init__(config, api_key)

    async def initialize(self) -> None:
        """Initialize test provider."""
        if not self._initialized:
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup test provider."""
        self._initialized = False

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from test provider.

        Args:
            messages: List of messages to send to provider
            model: Optional model to use
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens parameter

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError("Provider not initialized", provider="test")
        yield AIResponse(
            content="test",
            metadata=cast(ResponseMetadata, {
                "model": model or self.config["model"],
                "provider": "test",
                "usage": {"total_tokens": 0},
                "finish_reason": "stop",
            }),
        )
