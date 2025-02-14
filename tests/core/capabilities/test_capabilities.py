"""Tests for capabilities functionality."""

import pytest

from pepperpy.core.capabilities import (
    CapabilityContext,
    CapabilityError,
    CapabilityResult,
    CapabilityType,
)

from .conftest import MockCapability, TestCapabilityConfig


@pytest.mark.asyncio
async def test_capability_basic(mock_capability: MockCapability):
    """Test basic capability functionality."""
    # Test initial state
    assert mock_capability.type == CapabilityType.TOOLS
    assert isinstance(mock_capability.config, TestCapabilityConfig)
    assert isinstance(mock_capability.context, CapabilityContext)
    assert mock_capability.context.type == CapabilityType.TOOLS


@pytest.mark.asyncio
async def test_capability_lifecycle(mock_capability: MockCapability):
    """Test capability lifecycle methods."""
    # Test initialization
    await mock_capability.initialize()
    assert mock_capability.initialize_called
    assert mock_capability.validate_called

    # Test execution
    result = await mock_capability.execute(test_param="value")
    assert mock_capability.execute_called
    assert mock_capability.execute_kwargs == {"test_param": "value"}
    assert isinstance(result, CapabilityResult)
    assert result.success

    # Test cleanup
    await mock_capability.cleanup()
    assert mock_capability.cleanup_called
    assert not mock_capability.context.state  # State should be cleared


@pytest.mark.asyncio
async def test_capability_context(mock_capability: MockCapability):
    """Test capability context management."""
    # Test context initialization
    assert mock_capability.context.type == CapabilityType.TOOLS
    assert not mock_capability.context.state
    assert not mock_capability.context.metadata

    # Test context state management
    mock_capability.context.state["test_key"] = "test_value"
    assert mock_capability.context.state["test_key"] == "test_value"

    # Test context cleanup
    await mock_capability.cleanup()
    assert not mock_capability.context.state


@pytest.mark.asyncio
async def test_capability_error_handling(error_capability: MockCapability):
    """Test capability error handling."""
    # Test initialization error
    with pytest.raises(CapabilityError) as exc_info:
        await error_capability.initialize()
    assert str(exc_info.value) == "Initialization failed"
    assert exc_info.value.type == CapabilityType.TOOLS
    assert exc_info.value.details == {"error": "test error"}

    # Test validation error
    validate_error_capability = error_capability.__class__(
        type=CapabilityType.TOOLS,
        config=error_capability.config,
        **{"error_type": "validate"},
    )
    with pytest.raises(CapabilityError) as exc_info:
        await validate_error_capability.initialize()
    assert str(exc_info.value) == "Validation failed"

    # Test execution error
    execute_error_capability = error_capability.__class__(
        type=CapabilityType.TOOLS,
        config=error_capability.config,
        **{"error_type": "execute"},
    )
    with pytest.raises(CapabilityError) as exc_info:
        await execute_error_capability.execute()
    assert str(exc_info.value) == "Execution failed"


@pytest.mark.asyncio
async def test_capability_result():
    """Test capability result handling."""
    # Test successful result
    result = CapabilityResult(success=True, data={"key": "value"})
    assert result.success
    assert result.data == {"key": "value"}
    assert not result.error

    # Test failed result
    error = ValueError("Test error")
    result = CapabilityResult(
        success=False,
        error=error,
        metadata={"error_type": "validation"},
    )
    assert not result.success
    assert result.error == error
    assert result.metadata == {"error_type": "validation"}


@pytest.mark.asyncio
async def test_capability_config_validation():
    """Test capability configuration validation."""
    # Test valid configuration
    config = TestCapabilityConfig(name="test", value=42)
    capability = MockCapability(CapabilityType.TOOLS, config)
    await capability.validate()
    assert capability.validate_called

    # Test invalid configuration
    with pytest.raises(ValueError):
        TestCapabilityConfig(name="test", value="invalid")  # type: ignore


@pytest.mark.asyncio
async def test_capability_type_validation():
    """Test capability type validation."""
    # Test all capability types
    for capability_type in CapabilityType:
        config = TestCapabilityConfig()
        capability = MockCapability(capability_type, config)
        assert capability.type == capability_type
        assert capability.context.type == capability_type


@pytest.mark.asyncio
async def test_capability_execution_flow(mock_capability: MockCapability):
    """Test capability execution flow."""
    # Setup execution result
    mock_capability.execute_result = CapabilityResult(
        success=True,
        data={"result": "test"},
        metadata={"duration": 0.1},
    )

    # Initialize capability
    await mock_capability.initialize()
    assert mock_capability.initialize_called

    # Execute with parameters
    params = {"param1": "value1", "param2": "value2"}
    result = await mock_capability.execute(**params)

    # Verify execution
    assert mock_capability.execute_called
    assert mock_capability.execute_kwargs == params
    assert result.success
    assert result.data == {"result": "test"}
    assert result.metadata == {"duration": 0.1}

    # Cleanup
    await mock_capability.cleanup()
    assert mock_capability.cleanup_called
