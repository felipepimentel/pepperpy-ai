"""Tests for the unified capability system."""

from typing import Any, Dict, Optional

import pytest

from pepperpy.core.capabilities.base import (
    Capability,
    CapabilityContext,
    CapabilityProvider,
    CapabilityResult,
)
from pepperpy.core.capabilities.errors import (
    CapabilityError,
    CapabilityType,
    LearningError,
)


class TestCapability(Capability[Dict[str, Any], str]):
    """Test implementation of a capability."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(CapabilityType.LEARNING, config)
        self.execute_called = False
        self.cleanup_called = False
        self.initialize_called = False

    async def initialize(self) -> None:
        """Test initialization implementation."""
        self.initialize_called = True

    async def execute(
        self,
        context: CapabilityContext,
        **kwargs: Any,
    ) -> CapabilityResult[str]:
        """Test execution implementation."""
        self.execute_called = True
        if kwargs.get("fail"):
            raise LearningError("Test failure")
        return CapabilityResult(
            success=True,
            result="test_result",
            metadata={"test": "metadata"},
        )

    async def cleanup(self) -> None:
        """Test cleanup implementation."""
        self.cleanup_called = True


class TestProvider(CapabilityProvider):
    """Test implementation of a capability provider."""

    async def get_capability(
        self,
        capability_type: CapabilityType,
        config: Optional[Dict[str, Any]] = None,
    ) -> Capability[Any, Any]:
        """Get a test capability."""
        capability = TestCapability(config)
        await capability.initialize()
        return capability

    async def cleanup_capability(
        self,
        capability: Capability[Any, Any],
    ) -> None:
        """Clean up a test capability."""
        await capability.cleanup()


@pytest.mark.asyncio
async def test_capability_basic():
    """Test basic capability functionality."""
    config = {"test": "config"}
    capability = TestCapability(config)
    await capability.initialize()

    # Test initialization
    assert capability.capability_type == CapabilityType.LEARNING
    assert capability.config == config
    assert capability.initialize_called
    assert not capability.execute_called
    assert not capability.cleanup_called

    # Test execution
    context = CapabilityContext(
        capability_type=CapabilityType.LEARNING,
        metadata={"test": "metadata"},
    )
    result = await capability.execute(context)
    assert result.success
    assert result.result == "test_result"
    assert result.metadata == {"test": "metadata"}
    assert capability.execute_called

    # Test cleanup
    await capability.cleanup()
    assert capability.cleanup_called


@pytest.mark.asyncio
async def test_capability_error_handling():
    """Test capability error handling."""
    capability = TestCapability()
    await capability.initialize()
    context = CapabilityContext(
        capability_type=CapabilityType.LEARNING,
        metadata={},
    )

    # Test execution failure
    with pytest.raises(LearningError) as exc:
        await capability.execute(context, fail=True)
    assert exc.value.capability_type == CapabilityType.LEARNING
    assert str(exc.value).startswith("learning:")


@pytest.mark.asyncio
async def test_capability_validation():
    """Test capability validation."""
    # Test with missing config
    capability = TestCapability()
    await capability.initialize()
    with pytest.raises(CapabilityError) as exc:
        await capability.validate()
    assert exc.value.error_code == "CAPABILITY_CONFIG_MISSING"

    # Test with config
    capability = TestCapability({"test": "config"})
    await capability.initialize()
    await capability.validate()  # Should not raise


@pytest.mark.asyncio
async def test_capability_metadata():
    """Test capability metadata management."""
    capability = TestCapability()
    await capability.initialize()

    # Test adding metadata
    capability.add_metadata("test_key", "test_value")
    assert capability.get_metadata("test_key") == "test_value"

    # Test getting non-existent metadata
    assert capability.get_metadata("non_existent") is None


@pytest.mark.asyncio
async def test_capability_provider():
    """Test capability provider functionality."""
    provider = TestProvider()

    # Test getting capability
    capability = await provider.get_capability(
        CapabilityType.LEARNING,
        {"test": "config"},
    )
    assert isinstance(capability, TestCapability)
    assert capability.config == {"test": "config"}
    assert capability.initialize_called

    # Test cleanup
    await provider.cleanup_capability(capability)
    assert capability.cleanup_called


@pytest.mark.asyncio
async def test_capability_error_hierarchy():
    """Test capability error class hierarchy."""
    # Test base error
    error = CapabilityError(
        "Test error",
        CapabilityType.LEARNING,
        error_code="TEST_ERROR",
        details={"test": "details"},
    )
    assert error.capability_type == CapabilityType.LEARNING
    assert error.error_code == "TEST_ERROR"
    assert error.details == {"test": "details"}

    # Test specific error
    cause = ValueError("Original error")
    error = LearningError(
        "Test learning error",
        details={"test": "details"},
        cause=cause,
    )
    assert error.capability_type == CapabilityType.LEARNING
    assert error.error_code == "LEARNING_ERROR"
    assert error.cause == cause
