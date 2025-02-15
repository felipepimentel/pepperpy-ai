import pytest

from pepperpy.core.errors import LifecycleError, StateError
from pepperpy.core.lifecycle import (
    ComponentState,
    Lifecycle,
    LifecycleManager,
)


class TestComponent(Lifecycle):
    """Test implementation of a lifecycle-managed component."""

    def __init__(self) -> None:
        super().__init__()
        self.initialize_called = False
        self.cleanup_called = False
        self.start_called = False
        self.stop_called = False

    async def initialize(self) -> None:
        """Test initialization implementation."""
        self.initialize_called = True

    async def cleanup(self) -> None:
        """Test cleanup implementation."""
        self.cleanup_called = True

    async def start(self) -> None:
        """Test start implementation."""
        self.start_called = True

    async def stop(self) -> None:
        """Test stop implementation."""
        self.stop_called = True


class ErrorComponent(Lifecycle):
    """Test component that raises errors."""

    def __init__(self, raise_on_init: bool = True) -> None:
        super().__init__()
        self.raise_on_init = raise_on_init

    async def initialize(self) -> None:
        """Test initialization that raises an error."""
        if self.raise_on_init:
            raise ValueError("Test initialization error")

    async def cleanup(self) -> None:
        """Test cleanup that raises an error."""
        if not self.raise_on_init:
            raise ValueError("Test cleanup error")

    async def start(self) -> None:
        """Test start that raises an error."""
        if not self.raise_on_init:
            raise ValueError("Test start error")

    async def stop(self) -> None:
        """Test stop that raises an error."""
        if not self.raise_on_init:
            raise ValueError("Test stop error")


@pytest.mark.asyncio
async def test_lifecycle_basic():
    """Test basic lifecycle state transitions."""
    component = TestComponent()

    # Test initial state
    assert component.state == ComponentState.UNREGISTERED
    assert component.error is None
    assert isinstance(component._metadata, dict)

    # Test initialization
    await component.initialize()
    assert component.initialize_called

    # Test cleanup
    await component.cleanup()
    assert component.cleanup_called


@pytest.mark.asyncio
async def test_lifecycle_manager_registration():
    """Test component registration in lifecycle manager."""
    manager = LifecycleManager()
    component = TestComponent()

    # Test registration
    manager.register(component)
    assert component.id in manager._components
    assert component.state == ComponentState.REGISTERED

    # Test duplicate registration
    with pytest.raises(
        ValueError, match=f"Component {component.id} already registered"
    ):
        manager.register(component)


@pytest.mark.asyncio
async def test_lifecycle_manager_initialization():
    """Test component initialization through manager."""
    manager = LifecycleManager()
    component = TestComponent()

    # Register and initialize
    manager.register(component)
    await manager.initialize(component.id)
    assert component.state == ComponentState.INITIALIZED
    assert component.initialize_called


@pytest.mark.asyncio
async def test_lifecycle_manager_startup():
    """Test component startup through manager."""
    manager = LifecycleManager()
    component = TestComponent()

    # Setup and start component
    manager.register(component)
    await manager.initialize(component.id)
    await manager.start(component.id)
    assert component.state == ComponentState.RUNNING
    assert component.start_called
    assert manager.is_running(component.id)


@pytest.mark.asyncio
async def test_lifecycle_manager_shutdown():
    """Test lifecycle manager shutdown process."""
    manager = LifecycleManager()
    components = [TestComponent(), TestComponent()]

    # Register and start components
    for component in components:
        manager.register(component)
        await manager.initialize(component.id)
        await manager.start(component.id)

    # Test shutdown
    await manager.shutdown()

    # Verify all components are cleaned up
    for component in components:
        assert component.cleanup_called
        assert component.state == ComponentState.TERMINATED


@pytest.mark.asyncio
async def test_lifecycle_error_handling():
    """Test error handling in lifecycle components."""
    manager = LifecycleManager()

    # Test initialization error
    error_component = ErrorComponent(raise_on_init=True)
    manager.register(error_component)
    with pytest.raises(LifecycleError):
        await manager.initialize(error_component.id)
    assert error_component.state == ComponentState.ERROR

    # Test start error
    start_error_component = ErrorComponent(raise_on_init=False)
    manager.register(start_error_component)
    await manager.initialize(start_error_component.id)
    with pytest.raises(LifecycleError):
        await manager.start(start_error_component.id)
    assert start_error_component.state == ComponentState.ERROR

    # Test stop error
    stop_error_component = ErrorComponent(raise_on_init=False)
    manager.register(stop_error_component)
    await manager.initialize(stop_error_component.id)
    with pytest.raises(LifecycleError):
        await manager.stop(stop_error_component.id)
    assert stop_error_component.state == ComponentState.ERROR


@pytest.mark.asyncio
async def test_lifecycle_state_transitions():
    """Test lifecycle state transition validations."""
    manager = LifecycleManager()
    component = TestComponent()

    # Register component
    manager.register(component)
    assert component.state == ComponentState.REGISTERED

    # Test invalid transition: REGISTERED -> RUNNING
    with pytest.raises(StateError):
        await manager._update_state(component.id, ComponentState.RUNNING)

    # Test valid transitions
    await manager.initialize(component.id)
    assert component.state == ComponentState.INITIALIZED

    await manager.start(component.id)
    assert component.state == ComponentState.RUNNING

    await manager.stop(component.id)
    assert component.state == ComponentState.STOPPED

    await manager.terminate(component.id)
    assert component.state == ComponentState.TERMINATED
