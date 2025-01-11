"""Tests for base capabilities."""

import pytest
from typing import Any

from pepperpy_ai.capabilities.base import BaseCapability, CapabilityConfig
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse
from tests.providers import MockProvider


@pytest.fixture
def mock_capability_config():
    """Fixture that provides a mock capability config."""
    return CapabilityConfig(
        name="test_capability",
        description="Test capability description",
    )


@pytest.mark.asyncio
async def test_capability_initialization(
    mock_provider: BaseProvider,
    mock_capability_config: CapabilityConfig,
):
    """Test capability initialization."""
    
    class TestCapability(BaseCapability):
        """Test capability class."""
        async def initialize(self) -> None:
            """Initialize the capability."""
            pass
        
        async def cleanup(self) -> None:
            """Clean up resources."""
            pass
    
    capability = TestCapability(mock_capability_config, mock_provider)
    await capability.initialize()
    
    assert capability.config == mock_capability_config
    assert capability.provider == mock_provider
    
    await capability.cleanup()


@pytest.mark.asyncio
async def test_capability_registration():
    """Test capability registration."""
    
    class TestCapability(BaseCapability):
        """Test capability class."""
        async def initialize(self) -> None:
            """Initialize the capability."""
            pass
        
        async def cleanup(self) -> None:
            """Clean up resources."""
            pass
    
    assert isinstance(TestCapability, type)
    
    config = CapabilityConfig(
        name="test_capability",
        description="Test capability description",
    )
    provider = MockProvider()
    capability = TestCapability(config, provider)
    
    assert isinstance(capability, TestCapability)
    assert isinstance(capability, BaseCapability)
    assert capability.config == config
    assert capability.provider == provider
    
    await capability.initialize()
    await capability.cleanup()


@pytest.mark.asyncio
async def test_provider_methods(
    mock_provider: BaseProvider,
):
    """Test provider methods."""
    # Test complete method
    response = await mock_provider.complete("Test prompt")
    assert isinstance(response, AIResponse)
    assert response.content == "Mock completion"
    
    # Test stream method
    async for response in await mock_provider.stream("Test prompt"):
        assert isinstance(response, AIResponse)
        assert response.content == "Mock stream" 