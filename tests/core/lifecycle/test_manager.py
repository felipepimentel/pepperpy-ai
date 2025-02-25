"""Tests for lifecycle manager implementation."""

import pytest

from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.lifecycle.errors import (
    FinalizeError,
    InitializationError,
    StartError,
    StopError,
)
from pepperpy.core.lifecycle.manager import LifecycleManager
from pepperpy.core.lifecycle.types import (
    LifecycleConfig,
    LifecycleContext,
    LifecycleEvent,
    LifecycleState,
)


class DependentComponent(LifecycleComponent):
    """Test component with dependencies."""

    def __init__(self, name: str, should_fail: bool = False):
        super().__init__()
        self.name = name
        self.should_fail = should_fail
        self.initialize_called = False
        self.start_called = False
        self.stop_called = False
        self.cleanup_called = False

    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            await self._transition(
                LifecycleState.INITIALIZING, LifecycleEvent.INITIALIZE
            )
            await self._initialize()
            await self._transition(LifecycleState.READY, LifecycleEvent.INITIALIZE)
        except Exception as e:
            self.state = LifecycleState.ERROR
            self.context.error = e
            raise InitializationError(f"Failed to initialize: {e}") from e

    async def start(self) -> None:
        """Start the component."""
        try:
            await self._transition(LifecycleState.RUNNING, LifecycleEvent.START)
            await self._start()
        except Exception as e:
            self.state = LifecycleState.ERROR
            self.context.error = e
            raise StartError(f"Failed to start: {e}") from e

    async def stop(self) -> None:
        """Stop the component."""
        try:
            await self._transition(LifecycleState.STOPPING, LifecycleEvent.STOP)
            await self._stop()
            await self._transition(LifecycleState.STOPPED, LifecycleEvent.STOP)
        except Exception as e:
            self.state = LifecycleState.ERROR
            self.context.error = e
            raise StopError(f"Failed to stop: {e}") from e

    async def cleanup(self) -> None:
        """Clean up component resources."""
        try:
            await self._transition(LifecycleState.FINALIZING, LifecycleEvent.FINALIZE)
            await self._cleanup()
            await self._transition(LifecycleState.FINALIZED, LifecycleEvent.FINALIZE)
        except Exception as e:
            self.state = LifecycleState.ERROR
            self.context.error = e
            raise FinalizeError(f"Failed to finalize: {e}") from e

    async def _initialize(self) -> None:
        self.initialize_called = True
        if self.should_fail:
            raise RuntimeError(f"Test initialization failure: {self.name}")

    async def _start(self) -> None:
        self.start_called = True
        if self.should_fail:
            raise RuntimeError(f"Test start failure: {self.name}")

    async def _stop(self) -> None:
        self.stop_called = True
        if self.should_fail:
            raise RuntimeError(f"Test stop failure: {self.name}")

    async def _cleanup(self) -> None:
        self.cleanup_called = True
        if self.should_fail:
            raise RuntimeError(f"Test cleanup failure: {self.name}")


@pytest.mark.asyncio
async def test_manager_initialization():
    """Test lifecycle manager initialization."""
    manager = LifecycleManager()
    assert isinstance(manager.config, LifecycleConfig)
    assert isinstance(manager.context, LifecycleContext)
    assert len(manager.components) == 0
    assert len(manager.dependencies) == 0
    assert len(manager.hooks) == 2  # Default LoggingHook and MetricsHook


@pytest.mark.asyncio
async def test_component_registration():
    """Test component registration and dependency management."""
    manager = LifecycleManager()

    # Create components
    comp_a = DependentComponent("comp_a")
    comp_b = DependentComponent("comp_b")
    comp_c = DependentComponent("comp_c")

    # Register components with dependencies
    manager.register_component(comp_a)
    manager.register_component(comp_b, dependencies=["comp_a"])
    manager.register_component(comp_c, dependencies=["comp_b"])

    # Verify registration
    assert len(manager.components) == 3
    assert "comp_a" in manager.components
    assert "comp_b" in manager.components
    assert "comp_c" in manager.components

    # Verify dependencies
    assert not manager.dependencies["comp_a"]
    assert "comp_a" in manager.dependencies["comp_b"]
    assert "comp_b" in manager.dependencies["comp_c"]


@pytest.mark.asyncio
async def test_successful_lifecycle():
    """Test successful lifecycle operations with dependencies."""
    manager = LifecycleManager()

    # Create and register components
    comp_a = DependentComponent("comp_a")
    comp_b = DependentComponent("comp_b")
    manager.register_component(comp_a)
    manager.register_component(comp_b, dependencies=["comp_a"])

    # Initialize
    await manager.initialize()
    assert comp_a.initialize_called
    assert comp_b.initialize_called
    assert comp_a.state == LifecycleState.READY
    assert comp_b.state == LifecycleState.READY

    # Start
    await manager.start()
    assert comp_a.start_called
    assert comp_b.start_called
    assert comp_a.state == LifecycleState.RUNNING
    assert comp_b.state == LifecycleState.RUNNING

    # Stop
    await manager.stop()
    assert comp_a.stop_called
    assert comp_b.stop_called
    assert comp_a.state == LifecycleState.STOPPED
    assert comp_b.state == LifecycleState.STOPPED

    # Cleanup
    await manager.cleanup()
    assert comp_a.cleanup_called
    assert comp_b.cleanup_called
    assert comp_a.state == LifecycleState.FINALIZED
    assert comp_b.state == LifecycleState.FINALIZED


@pytest.mark.asyncio
async def test_failed_lifecycle():
    """Test lifecycle operations with component failures."""
    manager = LifecycleManager()

    # Create components with failures
    comp_a = DependentComponent("comp_a")
    comp_b = DependentComponent("comp_b", should_fail=True)
    manager.register_component(comp_a)
    manager.register_component(comp_b, dependencies=["comp_a"])

    # Test initialization failure
    with pytest.raises(InitializationError):
        await manager.initialize()
    assert comp_a.initialize_called
    assert comp_b.initialize_called
    assert comp_a.state == LifecycleState.READY
    assert comp_b.state == LifecycleState.ERROR

    # Reset components
    comp_a = DependentComponent("comp_a")
    comp_b = DependentComponent("comp_b", should_fail=True)
    manager.components.clear()
    manager.register_component(comp_a)
    manager.register_component(comp_b, dependencies=["comp_a"])
    await manager.initialize()

    # Test start failure
    with pytest.raises(StartError):
        await manager.start()
    assert comp_a.start_called
    assert comp_b.start_called
    assert comp_a.state == LifecycleState.RUNNING
    assert comp_b.state == LifecycleState.ERROR

    # Reset components
    comp_a = DependentComponent("comp_a")
    comp_b = DependentComponent("comp_b", should_fail=True)
    manager.components.clear()
    manager.register_component(comp_a)
    manager.register_component(comp_b, dependencies=["comp_a"])
    await manager.initialize()
    await manager.start()

    # Test stop failure
    with pytest.raises(StopError):
        await manager.stop()
    assert comp_a.stop_called
    assert comp_b.stop_called
    assert comp_b.state == LifecycleState.ERROR

    # Reset components
    comp_a = DependentComponent("comp_a")
    comp_b = DependentComponent("comp_b", should_fail=True)
    manager.components.clear()
    manager.register_component(comp_a)
    manager.register_component(comp_b, dependencies=["comp_a"])
    await manager.initialize()
    await manager.start()
    await manager.stop()

    # Test cleanup failure
    with pytest.raises(FinalizeError):
        await manager.cleanup()
    assert comp_a.cleanup_called
    assert comp_b.cleanup_called
    assert comp_b.state == LifecycleState.ERROR


@pytest.mark.asyncio
async def test_retry_operations():
    """Test retry operations in the manager."""
    manager = LifecycleManager()

    # Create components
    comp_a = DependentComponent("comp_a", should_fail=True)
    manager.register_component(comp_a)

    # Test retry initialization
    with pytest.raises(InitializationError):
        await manager.initialize()
    comp_a.should_fail = False
    await manager.retry("initialize")
    assert comp_a.state == LifecycleState.READY

    # Test retry start
    comp_a.should_fail = True
    with pytest.raises(StartError):
        await manager.start()
    comp_a.should_fail = False
    await manager.retry("start")
    assert comp_a.state == LifecycleState.RUNNING

    # Test retry stop
    comp_a.should_fail = True
    with pytest.raises(StopError):
        await manager.stop()
    comp_a.should_fail = False
    await manager.retry("stop")
    assert comp_a.state == LifecycleState.STOPPED

    # Test retry cleanup
    comp_a.should_fail = True
    with pytest.raises(FinalizeError):
        await manager.cleanup()
    comp_a.should_fail = False
    await manager.retry("cleanup")
    assert comp_a.state == LifecycleState.FINALIZED
