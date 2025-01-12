"""Test base capability functionality."""

from collections.abc import AsyncGenerator
from typing import Any, List, Optional, Type, cast

import pytest

from pepperpy_ai.ai_types import Message
from pepperpy_ai.capabilities.base import BaseCapability, CapabilityConfig
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse


class TestProvider(BaseProvider[CapabilityConfig]):
    """Test provider implementation."""

    async def initialize(self) -> None:
        """Initialize test provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup test provider."""
        self._initialized = False

    async def stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from test provider.

        Args:
            messages: List of messages to send to provider
            model: Optional model to use
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens parameter

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        yield AIResponse(content="test", provider="test", model=model or "test")


class TestCapability(BaseCapability[CapabilityConfig]):
    """Test capability implementation."""

    def __init__(self, config: CapabilityConfig, provider: Type[BaseProvider[Any]]) -> None:
        """Initialize test capability.

        Args:
            config: Capability configuration
            provider: Provider class to use
        """
        super().__init__(config, provider)
        self._provider_instance: Optional[BaseProvider[Any]] = None

    async def initialize(self) -> None:
        """Initialize test capability."""
        if not self._provider_instance:
            self._provider_instance = self.provider(self.config, "test-key")
            await self._provider_instance.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup test capability."""
        if self._provider_instance:
            await self._provider_instance.cleanup()
            self._provider_instance = None
            self._initialized = False

    def _ensure_initialized(self) -> BaseProvider[Any]:
        """Ensure capability is initialized.

        Returns:
            The initialized provider instance.

        Raises:
            RuntimeError: If capability is not initialized
        """
        if not self.is_initialized or not self._provider_instance:
            raise RuntimeError("Capability not initialized")
        return self._provider_instance

    async def stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from test provider.

        Args:
            messages: List of messages to send to provider
            model: Optional model to use
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens parameter

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        provider = self._ensure_initialized()

        async for response in provider.stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield response


@pytest.fixture
def test_config() -> CapabilityConfig:
    """Create test configuration.

    Returns:
        Test configuration
    """
    return CapabilityConfig(
        name="test",
        version="1.0.0",
        enabled=True,
        model_name="test",
        device="cpu",
        normalize_embeddings=True,
        batch_size=32,
    )


@pytest.fixture
def test_capability(test_config: CapabilityConfig) -> TestCapability:
    """Create test capability."""
    return TestCapability(test_config, TestProvider)


@pytest.mark.asyncio
async def test_capability_initialization(test_capability: TestCapability) -> None:
    """Test capability initialization."""
    try:
        # Initial state
        assert not test_capability.is_initialized

        # Initialize
        await test_capability.initialize()
        assert test_capability.is_initialized
    finally:
        # Cleanup
        await test_capability.cleanup()
        assert not test_capability.is_initialized
