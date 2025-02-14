"""Tests for the lifecycle management module."""

from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from pepperpy.core.errors import LifecycleError, StateError
from pepperpy.core.lifecycle import ComponentState, Lifecycle, LifecycleManager

from .conftest import MockComponent


class TestComponent(Lifecycle):
    """Test implementation of a lifecycle-managed component."""

    def __init__(self) -> None:
        super().__init__()
        self.initialize_called = False
        self.cleanup_called = False

    async def initialize(self) -> None:
        self.initialize_called = True

    async def cleanup(self) -> None:
        self.cleanup_called = True


@pytest.mark.asyncio
async def test_lifecycle_basic(mock_component: MockComponent):
    """Test basic lifecycle component functionality."""
    assert mock_component.state == ComponentState.UNREGISTERED
    assert mock_component.error is None
    assert isinstance(mock_component.id, UUID)


@pytest.mark.asyncio
async def test_lifecycle_manager_registration(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test component registration."""
    # Test registration
    lifecycle_manager.register(mock_component)
    assert mock_component.state == ComponentState.REGISTERED

    # Test duplicate registration
    with pytest.raises(ValueError):
        lifecycle_manager.register(mock_component)


@pytest.mark.asyncio
async def test_lifecycle_manager_initialization(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test component initialization."""
    lifecycle_manager.register(mock_component)
    await lifecycle_manager.initialize(mock_component.id)
    assert mock_component.state == ComponentState.INITIALIZED
    assert mock_component.initialize_called


@pytest.mark.asyncio
async def test_lifecycle_manager_startup(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test component startup."""
    lifecycle_manager.register(mock_component)
    await lifecycle_manager.initialize(mock_component.id)
    await lifecycle_manager.start(mock_component.id)
    assert mock_component.state == ComponentState.RUNNING
    assert mock_component.start_called


@pytest.mark.asyncio
async def test_lifecycle_manager_shutdown(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test component shutdown."""
    lifecycle_manager.register(mock_component)
    await lifecycle_manager.initialize(mock_component.id)
    await lifecycle_manager.start(mock_component.id)
    await lifecycle_manager.stop(mock_component.id)
    assert mock_component.state == ComponentState.STOPPED
    assert mock_component.stop_called


@pytest.mark.asyncio
async def test_lifecycle_manager_termination(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test component termination."""
    lifecycle_manager.register(mock_component)
    await lifecycle_manager.initialize(mock_component.id)
    await lifecycle_manager.terminate(mock_component.id)
    assert mock_component.state == ComponentState.TERMINATED
    assert mock_component.cleanup_called


@pytest.mark.asyncio
async def test_lifecycle_error_handling(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test error handling in lifecycle management."""
    lifecycle_manager.register(mock_component)

    # Test initialization error
    mock_component.initialize = AsyncMock(side_effect=RuntimeError("Init error"))
    with pytest.raises(LifecycleError):
        await lifecycle_manager.initialize(mock_component.id)
    assert mock_component.state == ComponentState.ERROR

    # Test start error
    mock_component.start = AsyncMock(side_effect=RuntimeError("Start error"))
    with pytest.raises(LifecycleError):
        await lifecycle_manager.start(mock_component.id)
    assert mock_component.state == ComponentState.ERROR

    # Test stop error
    mock_component.stop = AsyncMock(side_effect=RuntimeError("Stop error"))
    with pytest.raises(LifecycleError):
        await lifecycle_manager.stop(mock_component.id)
    assert mock_component.state == ComponentState.ERROR


@pytest.mark.asyncio
async def test_lifecycle_dependencies(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test component dependency management."""
    # Create two components
    component1 = mock_component
    component2 = MockComponent()

    # Register both components
    lifecycle_manager.register(component1)
    lifecycle_manager.register(component2)

    # Add dependency
    lifecycle_manager.add_dependency(component1.id, component2.id)
    deps = lifecycle_manager.get_dependencies(component1.id)
    assert component2.id in deps

    # Test invalid dependency
    with pytest.raises(ValueError):
        lifecycle_manager.add_dependency(UUID(int=0), component1.id)


@pytest.mark.asyncio
async def test_lifecycle_state_handlers(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test state change handlers."""
    handler_called = False
    test_state = None
    test_component = None

    def state_handler(component_id: UUID) -> None:
        nonlocal handler_called, test_state, test_component
        handler_called = True
        test_component = component_id

    # Add handler for INITIALIZED state
    lifecycle_manager.add_state_handler(ComponentState.INITIALIZED, state_handler)

    # Register and initialize component
    lifecycle_manager.register(mock_component)
    await lifecycle_manager.initialize(mock_component.id)

    # Verify handler was called
    assert handler_called
    assert test_component == mock_component.id

    # Remove handler and verify it's not called again
    handler_called = False
    lifecycle_manager.remove_state_handler(ComponentState.INITIALIZED, state_handler)
    await lifecycle_manager.initialize(mock_component.id)
    assert not handler_called


@pytest.mark.asyncio
async def test_lifecycle_invalid_transitions(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test invalid state transitions."""
    lifecycle_manager.register(mock_component)

    # Try to start without initializing
    with pytest.raises(StateError):
        await lifecycle_manager.start(mock_component.id)

    # Initialize and try to terminate while running
    await lifecycle_manager.initialize(mock_component.id)
    await lifecycle_manager.start(mock_component.id)
    with pytest.raises(StateError):
        await lifecycle_manager.terminate(mock_component.id)


@pytest.mark.asyncio
async def test_lifecycle_running_state(
    lifecycle_manager: LifecycleManager, mock_component: MockComponent
):
    """Test running state checks."""
    lifecycle_manager.register(mock_component)
    assert not lifecycle_manager.is_running(mock_component.id)

    await lifecycle_manager.initialize(mock_component.id)
    assert not lifecycle_manager.is_running(mock_component.id)

    await lifecycle_manager.start(mock_component.id)
    assert lifecycle_manager.is_running(mock_component.id)

    await lifecycle_manager.stop(mock_component.id)
    assert not lifecycle_manager.is_running(mock_component.id)
