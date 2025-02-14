"""Tests for capability provider functionality."""

from typing import Dict, Optional

import pytest
from pydantic import BaseModel

from pepperpy.core.capabilities import Capability, CapabilityType
from pepperpy.core.capabilities.errors import (
    CapabilityConfigError,
    CapabilityNotFoundError,
)
from pepperpy.core.capabilities.types import CapabilityProvider

from .conftest import MockCapability, TestCapabilityConfig


class MockProvider(CapabilityProvider):
    """Mock capability provider for testing."""

    def __init__(self) -> None:
        self._capabilities: Dict[CapabilityType, type[Capability]] = {
            CapabilityType.TOOLS: MockCapability,
        }

    async def get_capability(
        self,
        type: CapabilityType,
        config: Optional[BaseModel] = None,
    ) -> Capability:
        """Get a capability instance."""
        if type not in self._capabilities:
            raise CapabilityNotFoundError(type)

        if config is None:
            config = TestCapabilityConfig()
        elif not isinstance(config, TestCapabilityConfig):
            raise CapabilityConfigError(
                "Invalid configuration type",
                type,
                config_key="config_type",
                details={"expected": "TestCapabilityConfig"},
            )

        return self._capabilities[type](type, config)

    async def list_capabilities(self) -> Dict[CapabilityType, type[Capability]]:
        """List available capabilities."""
        return self._capabilities.copy()


@pytest.fixture
def mock_provider() -> MockProvider:
    """Provide mock provider instance."""
    return MockProvider()


@pytest.mark.asyncio
async def test_provider_basic(mock_provider: MockProvider):
    """Test basic provider functionality."""
    # Test capability listing
    capabilities = await mock_provider.list_capabilities()
    assert CapabilityType.TOOLS in capabilities
    assert capabilities[CapabilityType.TOOLS] == MockCapability


@pytest.mark.asyncio
async def test_provider_get_capability(mock_provider: MockProvider):
    """Test getting capabilities from provider."""
    # Test with default config
    capability = await mock_provider.get_capability(CapabilityType.TOOLS)
    assert isinstance(capability, MockCapability)
    assert capability.type == CapabilityType.TOOLS
    assert isinstance(capability.config, TestCapabilityConfig)

    # Test with custom config
    config = TestCapabilityConfig(name="custom", value=100)
    capability = await mock_provider.get_capability(CapabilityType.TOOLS, config)
    assert capability.config.name == "custom"
    assert capability.config.value == 100


@pytest.mark.asyncio
async def test_provider_error_handling(mock_provider: MockProvider):
    """Test provider error handling."""
    # Test capability not found
    with pytest.raises(CapabilityNotFoundError) as exc_info:
        await mock_provider.get_capability(CapabilityType.LEARNING)
    assert exc_info.value.type == CapabilityType.LEARNING

    # Test invalid configuration
    class InvalidConfig(BaseModel):
        value: str

    with pytest.raises(CapabilityConfigError) as exc_info:
        await mock_provider.get_capability(
            CapabilityType.TOOLS,
            InvalidConfig(value="test"),
        )
    assert exc_info.value.type == CapabilityType.TOOLS
    assert exc_info.value.config_key == "config_type"


@pytest.mark.asyncio
async def test_provider_capability_lifecycle(mock_provider: MockProvider):
    """Test capability lifecycle through provider."""
    # Get capability
    capability = await mock_provider.get_capability(CapabilityType.TOOLS)
    assert isinstance(capability, MockCapability)

    # Initialize capability
    await capability.initialize()
    assert capability.initialize_called

    # Execute capability
    result = await capability.execute(test=True)
    assert capability.execute_called
    assert result.success

    # Cleanup capability
    await capability.cleanup()
    assert capability.cleanup_called
