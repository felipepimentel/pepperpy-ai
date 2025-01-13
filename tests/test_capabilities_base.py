"""Test base capability functionality."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest

from pepperpy_ai.ai_types import Message, MessageRole
from pepperpy_ai.capabilities.base import BaseCapability
from pepperpy_ai.config.capability import CapabilityConfig
from pepperpy_ai.exceptions import ProviderError
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse


class TestProvider(BaseProvider[Any]):
    """Test provider."""

    def __init__(self, config: CapabilityConfig) -> None:
        """Initialize test provider."""
        super().__init__(config, api_key="test")
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up provider."""
        self._initialized = False

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses."""
        if not self._initialized:
            raise ProviderError("Provider not initialized", provider="test", operation="stream")
        yield AIResponse(content="test")


class TestCapability(BaseCapability[TestProvider]):
    """Test capability implementation."""

    def __init__(
        self,
        config: CapabilityConfig,
        provider: type[TestProvider],
    ) -> None:
        """Initialize capability.

        Args:
            config: Capability configuration
            provider: Provider class to use
        """
        super().__init__(config, provider)
        self._provider_instance: TestProvider | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize capability."""
        if not self._initialized:
            self._provider_instance = self.provider(self.config)
            await self._provider_instance.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup capability."""
        if self._initialized and self._provider_instance:
            await self._provider_instance.cleanup()
            self._provider_instance = None
            self._initialized = False


@pytest.mark.asyncio
async def test_capability_initialization() -> None:
    """Test capability initialization."""
    config = CapabilityConfig(name="test", version="1.0")
    capability = TestCapability(config, TestProvider)

    try:
        assert not capability.is_initialized
        await capability.initialize()
        assert capability.is_initialized
    finally:
        await capability.cleanup()
        assert not capability.is_initialized


@pytest.mark.asyncio
async def test_provider_streaming() -> None:
    """Test provider streaming."""
    config = CapabilityConfig(name="test", version="1.0.0")
    provider = TestProvider(config)

    try:
        await provider.initialize()
        messages = [Message(role=MessageRole.USER, content="test")]
        responses = []
        async for response in provider.stream(messages):
            responses.append(response)

        assert len(responses) == 1
        assert responses[0].content == "test"
    finally:
        await provider.cleanup()
