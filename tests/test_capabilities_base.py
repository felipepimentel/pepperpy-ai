"""Test base capability module."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest

from pepperpy_ai.ai_types import Message
from pepperpy_ai.capabilities.base import BaseCapability
from pepperpy_ai.config.capability import CapabilityConfig
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse


class TestProvider(BaseProvider[Any]):
    """Test provider implementation."""

    def __init__(self, config: CapabilityConfig, api_key: str = "") -> None:
        """Initialize provider.

        Args:
            config: Provider configuration.
            api_key: API key, defaults to empty string.
        """
        super().__init__(config, api_key)

    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        self._initialized = False

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses."""
        yield AIResponse(content="test response")


class TestCapability(BaseCapability[TestProvider]):
    """Test capability implementation."""

    def __init__(
        self,
        config: CapabilityConfig,
        provider: type[TestProvider],
    ) -> None:
        """Initialize test capability.

        Args:
            config: Capability configuration.
            provider: Provider class.
        """
        super().__init__(config, provider)
        self._provider_instance: TestProvider | None = None

    async def initialize(self) -> None:
        """Initialize capability."""
        if not self._provider_instance:
            self._provider_instance = self.provider(self.config)
            await self._provider_instance.initialize()
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup capability resources."""
        if self._provider_instance:
            await self._provider_instance.cleanup()
            self._provider_instance = None
        self._initialized = False


@pytest.mark.asyncio
async def test_capability_initialization() -> None:
    """Test that capability can be initialized."""
    config = CapabilityConfig(name="test", version="1.0")
    capability = TestCapability(config, TestProvider)
    assert not capability.is_initialized
    await capability.initialize()
    assert capability.is_initialized
    await capability.cleanup()
    assert not capability.is_initialized
