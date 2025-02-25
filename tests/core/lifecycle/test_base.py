"""Tests for base lifecycle component implementation."""

import pytest

from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.lifecycle.errors import (
    FinalizeError,
    InitializationError,
    StartError,
    StateError,
    StopError,
)
from pepperpy.core.lifecycle.types import (
    LifecycleConfig,
    LifecycleContext,
    LifecycleEvent,
    LifecycleState,
)


class TestComponent(LifecycleComponent):
    """Test component for lifecycle testing."""

    def __init__(self, should_fail: bool = False):
        super().__init__()
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
            raise RuntimeError("Test initialization failure")

    async def _start(self) -> None:
        self.start_called = True
        if self.should_fail:
            raise RuntimeError("Test start failure")

    async def _stop(self) -> None:
        self.stop_called = True
        if self.should_fail:
            raise RuntimeError("Test stop failure")

    async def _cleanup(self) -> None:
        self.cleanup_called = True
        if self.should_fail:
            raise RuntimeError("Test cleanup failure")


@pytest.mark.asyncio
async def test_initial_state():
    """Test initial component state."""
    component = TestComponent()
    assert component.state == LifecycleState.UNINITIALIZED
    assert isinstance(component.config, LifecycleConfig)
    assert isinstance(component.context, LifecycleContext)
    assert len(component.hooks) == 0
    assert len(component.metrics.transitions) == 0


@pytest.mark.asyncio
async def test_successful_lifecycle():
    """Test successful lifecycle operations."""
    component = TestComponent()

    # Initialize
    await component.initialize()
    assert component.initialize_called
    assert component.state == LifecycleState.READY
    assert (
        len(component.metrics.transitions) == 2
    )  # UNINITIALIZED -> INITIALIZING -> READY

    # Start
    await component.start()
    assert component.start_called
    assert component.state == LifecycleState.RUNNING
    assert len(component.metrics.transitions) == 3

    # Stop
    await component.stop()
    assert component.stop_called
    assert component.state == LifecycleState.STOPPED
    assert len(component.metrics.transitions) == 5  # Including STOPPING state

    # Cleanup
    await component.cleanup()
    assert component.cleanup_called
    assert component.state == LifecycleState.FINALIZED
    assert len(component.metrics.transitions) == 7  # Including FINALIZING state


@pytest.mark.asyncio
async def test_failed_lifecycle():
    """Test lifecycle operations with failures."""
    component = TestComponent(should_fail=True)

    # Test initialization failure
    with pytest.raises(InitializationError):
        await component.initialize()
    assert component.initialize_called
    assert component.state == LifecycleState.ERROR

    # Reset component
    component = TestComponent(should_fail=True)
    await component.initialize()

    # Test start failure
    with pytest.raises(StartError):
        await component.start()
    assert component.start_called
    assert component.state == LifecycleState.ERROR

    # Reset component
    component = TestComponent(should_fail=True)
    await component.initialize()
    await component.start()

    # Test stop failure
    with pytest.raises(StopError):
        await component.stop()
    assert component.stop_called
    assert component.state == LifecycleState.ERROR

    # Reset component
    component = TestComponent(should_fail=True)
    await component.initialize()
    await component.start()
    await component.stop()

    # Test cleanup failure
    with pytest.raises(FinalizeError):
        await component.cleanup()
    assert component.cleanup_called
    assert component.state == LifecycleState.ERROR


@pytest.mark.asyncio
async def test_invalid_transitions():
    """Test invalid state transitions."""
    component = TestComponent()

    # Cannot start without initialization
    with pytest.raises(StateError):
        await component.start()

    # Cannot stop without starting
    await component.initialize()
    with pytest.raises(StateError):
        await component.stop()

    # Cannot cleanup without stopping
    await component.start()
    with pytest.raises(StateError):
        await component.cleanup()

    # Cannot initialize twice
    with pytest.raises(StateError):
        await component.initialize()


@pytest.mark.asyncio
async def test_retry_operation():
    """Test retry operation functionality."""
    component = TestComponent(should_fail=True)

    # Test retry initialization
    with pytest.raises(InitializationError):
        await component.initialize()
    component.should_fail = False
    await component.retry("initialize")
    assert component.state == LifecycleState.READY

    # Test retry start
    component.should_fail = True
    with pytest.raises(StartError):
        await component.start()
    component.should_fail = False
    await component.retry("start")
    assert component.state == LifecycleState.RUNNING

    # Test retry stop
    component.should_fail = True
    with pytest.raises(StopError):
        await component.stop()
    component.should_fail = False
    await component.retry("stop")
    assert component.state == LifecycleState.STOPPED

    # Test retry cleanup
    component.should_fail = True
    with pytest.raises(FinalizeError):
        await component.cleanup()
    component.should_fail = False
    await component.retry("cleanup")
    assert component.state == LifecycleState.FINALIZED
