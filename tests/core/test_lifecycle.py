from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from pepperpy.core.errors import LifecycleError, StateError
from pepperpy.core.lifecycle import (
    ComponentState,
    Lifecycle,
    LifecycleManager,
)


class TestComponent(Lifecycle):
    """Test component implementing the Lifecycle interface."""

    def __init__(self):
        """Initialize the test component."""
        super().__init__()
        self.initialize_called = False
        self.cleanup_called = False
        self.start_called = False
        self.stop_called = False

    async def initialize(self) -> None:
        """Initialize the component."""
        self.initialize_called = True

    async def cleanup(self) -> None:
        """Clean up component resources."""
        self.cleanup_called = True

    async def start(self) -> None:
        """Start the component."""
        self.start_called = True

    async def stop(self) -> None:
        """Stop the component."""
        self.stop_called = True


@pytest.mark.asyncio
async def test_lifecycle_basic():
    """Test basic lifecycle functionality."""
    component = TestComponent()
    assert component.state == ComponentState.UNREGISTERED
    assert component.error is None

    await component.initialize()
    assert component.initialize_called
    assert not component.cleanup_called

    await component.cleanup()
    assert component.cleanup_called


@pytest.mark.asyncio
async def test_lifecycle_manager():
    """Test lifecycle manager functionality."""
    manager = LifecycleManager()
    component = TestComponent()

    # Test registration
    manager.register(component)
    assert component.state == ComponentState.REGISTERED
    assert not component.initialize_called

    # Test initialization
    await manager.initialize(component.id)
    assert component.state == ComponentState.INITIALIZED
    assert component.initialize_called

    # Test starting
    await manager.start(component.id)
    assert component.state == ComponentState.RUNNING
    assert component.start_called

    # Test stopping
    await manager.stop(component.id)
    assert component.state == ComponentState.STOPPED
    assert component.stop_called

    # Test duplicate registration
    with pytest.raises(ValueError):
        manager.register(component)

    # Test component retrieval
    retrieved = manager._components.get(component.id)
    assert retrieved is component

    # Test non-existent component retrieval
    assert manager._components.get(uuid4()) is None

    # Test shutdown
    await manager.shutdown()
    assert component.state == ComponentState.TERMINATED
    assert component.cleanup_called


@pytest.mark.asyncio
async def test_lifecycle_error_handling():
    """Test lifecycle error handling."""
    manager = LifecycleManager()

    # Test initialization error
    error_component = TestComponent()
    error_component.initialize = AsyncMock(side_effect=RuntimeError("Init error"))

    manager.register(error_component)
    with pytest.raises(LifecycleError):
        await manager.initialize(error_component.id)
    assert error_component.state == ComponentState.ERROR
    assert isinstance(error_component.error, RuntimeError)
    assert str(error_component.error) == "Init error"

    # Test start error
    start_error_component = TestComponent()
    manager.register(start_error_component)
    await manager.initialize(start_error_component.id)
    start_error_component.start = AsyncMock(side_effect=RuntimeError("Start error"))

    with pytest.raises(LifecycleError):
        await manager.start(start_error_component.id)
    assert start_error_component.state == ComponentState.ERROR
    assert isinstance(start_error_component.error, RuntimeError)
    assert str(start_error_component.error) == "Start error"

    # Test stop error
    stop_error_component = TestComponent()
    manager.register(stop_error_component)
    await manager.initialize(stop_error_component.id)
    await manager.start(stop_error_component.id)
    stop_error_component.stop = AsyncMock(side_effect=RuntimeError("Stop error"))

    with pytest.raises(LifecycleError):
        await manager.stop(stop_error_component.id)
    assert stop_error_component.state == ComponentState.ERROR
    assert isinstance(stop_error_component.error, RuntimeError)
    assert str(stop_error_component.error) == "Stop error"

    # Test cleanup error
    component = TestComponent()
    manager.register(component)
    await manager.initialize(component.id)
    component.cleanup = AsyncMock(side_effect=RuntimeError("Cleanup error"))

    await manager.shutdown()
    assert component.state == ComponentState.ERROR
    assert isinstance(component.error, RuntimeError)
    assert str(component.error) == "Cleanup error"


@pytest.mark.asyncio
async def test_lifecycle_metadata():
    """Test lifecycle metadata management."""
    component = TestComponent()
    assert not component._metadata

    # Set metadata
    component._metadata["test_key"] = "test_value"
    assert component._metadata["test_key"] == "test_value"

    # Update metadata
    component._metadata.update({
        "key1": "value1",
        "key2": "value2",
    })
    assert component._metadata["key1"] == "value1"
    assert component._metadata["key2"] == "value2"

    # Clear metadata
    component._metadata.clear()
    assert not component._metadata


@pytest.mark.asyncio
async def test_lifecycle_manager_shutdown_order():
    """Test that components are shut down in reverse registration order."""
    manager = LifecycleManager()
    shutdown_order = []

    class OrderedComponent(TestComponent):
        def __init__(self, name: str):
            super().__init__()
            self.name = name

        async def cleanup(self) -> None:
            await super().cleanup()
            shutdown_order.append(self.name)

    # Register components
    components = []
    for i in range(3):
        component = OrderedComponent(f"component{i}")
        manager.register(component)
        await manager.initialize(component.id)
        await manager.start(component.id)
        components.append(component)

    # Shutdown and verify order
    await manager.shutdown()
    assert shutdown_order == ["component2", "component1", "component0"]


@pytest.mark.asyncio
async def test_lifecycle_state_transitions():
    """Test component state transitions through its lifecycle."""
    manager = LifecycleManager()
    component = TestComponent()

    # Initial state
    assert component.state == ComponentState.UNREGISTERED

    # Registration
    manager.register(component)
    assert component.state == ComponentState.REGISTERED

    # Initialization
    await manager.initialize(component.id)
    assert component.state == ComponentState.INITIALIZED

    # Start
    await manager.start(component.id)
    assert component.state == ComponentState.RUNNING

    # Stop
    await manager.stop(component.id)
    assert component.state == ComponentState.STOPPED

    # Restart
    await manager.start(component.id)
    assert component.state == ComponentState.RUNNING

    # Invalid transition test
    with pytest.raises(StateError):
        await manager._update_state(component.id, ComponentState.REGISTERED)

    # Terminate
    await manager.terminate(component.id)
    assert component.state == ComponentState.TERMINATED

    # Cannot transition from terminated
    with pytest.raises(StateError):
        await manager._update_state(component.id, ComponentState.RUNNING)
