"""Tests for the base lifecycle module."""

import asyncio
import pytest
from datetime import datetime

from pepperpy.core.errors.unified import (
    ComponentError,
    LifecycleError,
    StateError,
)
from pepperpy.core.lifecycle.base import (
    Lifecycle,
    LifecycleComponent,
    LifecycleHook,
    LifecycleState,
    LifecycleTransition,
)


class TestHook(LifecycleHook):
    """Test hook implementation."""

    def __init__(self) -> None:
        """Initialize test hook."""
        self.pre_initialize_called = False
        self.post_initialize_called = False
        self.pre_cleanup_called = False
        self.post_cleanup_called = False
        self.error_called = False
        self.last_error: Exception | None = None

    async def pre_initialize(self, component: LifecycleComponent) -> None:
        """Called before initialization."""
        self.pre_initialize_called = True

    async def post_initialize(self, component: LifecycleComponent) -> None:
        """Called after initialization."""
        self.post_initialize_called = True

    async def pre_cleanup(self, component: LifecycleComponent) -> None:
        """Called before cleanup."""
        self.pre_cleanup_called = True

    async def post_cleanup(self, component: LifecycleComponent) -> None:
        """Called after cleanup."""
        self.post_cleanup_called = True

    async def on_error(self, component: LifecycleComponent, error: Exception) -> None:
        """Called when an error occurs."""
        self.error_called = True
        self.last_error = error


class TestComponent(LifecycleComponent):
    """Test component implementation."""

    def __init__(
        self, name: str, fail_initialize: bool = False, fail_cleanup: bool = False
    ) -> None:
        """Initialize test component.

        Args:
            name: Component name
            fail_initialize: Whether to fail initialization
            fail_cleanup: Whether to fail cleanup
        """
        super().__init__(name)
        self.fail_initialize = fail_initialize
        self.fail_cleanup = fail_cleanup
        self.initialize_called = False
        self.cleanup_called = False

    async def _initialize(self) -> None:
        """Initialize the component."""
        self.initialize_called = True
        if self.fail_initialize:
            raise ValueError("Initialization failed")

    async def _cleanup(self) -> None:
        """Clean up the component."""
        self.cleanup_called = True
        if self.fail_cleanup:
            raise ValueError("Cleanup failed")


@pytest.mark.asyncio
async def test_lifecycle_state_transitions():
    """Test lifecycle state transitions."""
    component = TestComponent("test")

    # Initial state
    assert component.state == LifecycleState.UNINITIALIZED
    assert len(component.transitions) == 0

    # Initialize
    await component.initialize()
    assert component.state == LifecycleState.INITIALIZED
    assert len(component.transitions) == 2
    assert component.transitions[0].from_state == LifecycleState.UNINITIALIZED
    assert component.transitions[0].to_state == LifecycleState.INITIALIZING
    assert component.transitions[1].from_state == LifecycleState.INITIALIZING
    assert component.transitions[1].to_state == LifecycleState.INITIALIZED

    # Cleanup
    await component.cleanup()
    assert component.state == LifecycleState.FINALIZED
    assert len(component.transitions) == 4
    assert component.transitions[2].from_state == LifecycleState.INITIALIZED
    assert component.transitions[2].to_state == LifecycleState.FINALIZING
    assert component.transitions[3].from_state == LifecycleState.FINALIZING
    assert component.transitions[3].to_state == LifecycleState.FINALIZED


@pytest.mark.asyncio
async def test_lifecycle_hooks():
    """Test lifecycle hooks."""
    component = TestComponent("test")
    hook = TestHook()
    component.add_hook(hook)

    # Initialize
    await component.initialize()
    assert hook.pre_initialize_called
    assert hook.post_initialize_called
    assert not hook.error_called

    # Cleanup
    await component.cleanup()
    assert hook.pre_cleanup_called
    assert hook.post_cleanup_called
    assert not hook.error_called


@pytest.mark.asyncio
async def test_lifecycle_error_handling():
    """Test lifecycle error handling."""
    component = TestComponent("test", fail_initialize=True)
    hook = TestHook()
    component.add_hook(hook)

    # Initialize (should fail)
    with pytest.raises(LifecycleError) as exc_info:
        await component.initialize()

    assert component.state == LifecycleState.ERROR
    assert hook.error_called
    assert isinstance(hook.last_error, ValueError)
    assert "Initialization failed" in str(exc_info.value)

    # Metadata should be updated
    assert "error" in component.metadata
    assert "Initialization failed" in component.metadata["error"]


@pytest.mark.asyncio
async def test_lifecycle_invalid_transitions():
    """Test invalid lifecycle transitions."""
    component = TestComponent("test")

    # Cannot cleanup uninitialized component
    with pytest.raises(StateError):
        await component.cleanup()

    # Cannot initialize twice
    await component.initialize()
    with pytest.raises(StateError):
        await component.initialize()

    # Cannot cleanup twice
    await component.cleanup()
    with pytest.raises(StateError):
        await component.cleanup()


@pytest.mark.asyncio
async def test_lifecycle_metadata():
    """Test lifecycle metadata."""
    component = TestComponent("test")

    # Initial metadata
    assert component.metadata["name"] == "test"
    assert isinstance(component.metadata["created_at"], datetime)
    assert isinstance(component.metadata["updated_at"], datetime)

    # After initialization
    created_at = component.metadata["created_at"]
    await asyncio.sleep(0.1)  # Ensure time difference
    await component.initialize()
    assert component.metadata["created_at"] == created_at
    assert component.metadata["updated_at"] > created_at


@pytest.mark.asyncio
async def test_lifecycle_hook_management():
    """Test lifecycle hook management."""
    component = TestComponent("test")
    hook1 = TestHook()
    hook2 = TestHook()

    # Add hooks
    component.add_hook(hook1)
    component.add_hook(hook2)
    assert len(component.hooks) == 2

    # Remove hook
    component.remove_hook(hook1)
    assert len(component.hooks) == 1
    assert hook2 in component.hooks

    # Initialize should only call remaining hook
    await component.initialize()
    assert not hook1.pre_initialize_called
    assert hook2.pre_initialize_called


@pytest.mark.asyncio
async def test_lifecycle_wait_ready():
    """Test wait_ready functionality."""
    component = TestComponent("test")

    # Cannot wait on uninitialized component
    with pytest.raises(NotImplementedError):
        await component.wait_ready()

    # Initialize and wait
    await component.initialize()
    await component.wait_ready()  # Should return immediately

    # Error state
    component = TestComponent("test", fail_initialize=True)
    with pytest.raises(LifecycleError):
        await component.initialize()
    with pytest.raises(StateError):
        await component.wait_ready()


def test_lifecycle_transition_str():
    """Test LifecycleTransition string representation."""
    transition = LifecycleTransition(
        LifecycleState.UNINITIALIZED, LifecycleState.INITIALIZING
    )
    assert str(transition) == "uninitialized -> initializing" 