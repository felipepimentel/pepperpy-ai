"""Tests for the unified lifecycle management system."""

import pytest

from pepperpy.core.lifecycle.base import LifecycleComponent, LifecycleHook
from pepperpy.core.lifecycle.errors import (
    ComponentAlreadyExistsError,
    ComponentNotFoundError,
)
from pepperpy.core.lifecycle.managers.pool import get_component_pool
from pepperpy.core.lifecycle.monitors.state import get_state_monitor
from pepperpy.core.lifecycle.types import LifecycleState, StateTransition


class TestComponent(LifecycleComponent):
    """Test implementation of LifecycleComponent."""

    async def _do_initialize(self) -> None:
        self.set_metadata("initialized", True)

    async def _do_start(self) -> None:
        self.set_metadata("started", True)

    async def _do_stop(self) -> None:
        self.set_metadata("stopped", True)

    async def _do_finalize(self) -> None:
        self.set_metadata("finalized", True)


class TestHook(LifecycleHook):
    """Test implementation of LifecycleHook."""

    def __init__(self):
        self.calls = []

    async def pre_init(self) -> None:
        self.calls.append("pre_init")

    async def post_init(self) -> None:
        self.calls.append("post_init")

    async def pre_start(self) -> None:
        self.calls.append("pre_start")

    async def post_start(self) -> None:
        self.calls.append("post_start")

    async def pre_stop(self) -> None:
        self.calls.append("pre_stop")

    async def post_stop(self) -> None:
        self.calls.append("post_stop")

    async def pre_finalize(self) -> None:
        self.calls.append("pre_finalize")

    async def post_finalize(self) -> None:
        self.calls.append("post_finalize")


def test_lifecycle_states():
    """Test lifecycle state enumeration."""
    assert LifecycleState.UNINITIALIZED.value == "uninitialized"
    assert LifecycleState.INITIALIZING.value == "initializing"
    assert LifecycleState.INITIALIZED.value == "initialized"
    assert LifecycleState.STARTING.value == "starting"
    assert LifecycleState.RUNNING.value == "running"
    assert LifecycleState.STOPPING.value == "stopping"
    assert LifecycleState.STOPPED.value == "stopped"
    assert LifecycleState.FINALIZING.value == "finalizing"
    assert LifecycleState.FINALIZED.value == "finalized"
    assert LifecycleState.ERROR.value == "error"


def test_state_transition():
    """Test state transition validation."""
    # Valid transitions
    assert StateTransition(
        LifecycleState.UNINITIALIZED, LifecycleState.INITIALIZING
    ).is_valid()

    assert StateTransition(
        LifecycleState.INITIALIZING, LifecycleState.INITIALIZED
    ).is_valid()

    # Invalid transitions
    assert not StateTransition(
        LifecycleState.UNINITIALIZED, LifecycleState.RUNNING
    ).is_valid()

    assert not StateTransition(
        LifecycleState.RUNNING, LifecycleState.INITIALIZING
    ).is_valid()


@pytest.mark.asyncio
async def test_lifecycle_component():
    """Test lifecycle component functionality."""
    component = TestComponent("test")
    hook = TestHook()
    component.add_hook(hook)

    # Test initial state
    assert component.state == LifecycleState.UNINITIALIZED
    assert not component.get_metadata("initialized")

    # Test initialization
    await component.initialize()
    assert component.state == LifecycleState.INITIALIZED
    assert component.get_metadata("initialized")
    assert "pre_init" in hook.calls
    assert "post_init" in hook.calls

    # Test start
    await component.start()
    assert component.state == LifecycleState.RUNNING
    assert component.get_metadata("started")
    assert "pre_start" in hook.calls
    assert "post_start" in hook.calls

    # Test stop
    await component.stop()
    assert component.state == LifecycleState.STOPPED
    assert component.get_metadata("stopped")
    assert "pre_stop" in hook.calls
    assert "post_stop" in hook.calls

    # Test finalization
    await component.finalize()
    assert component.state == LifecycleState.FINALIZED
    assert component.get_metadata("finalized")
    assert "pre_finalize" in hook.calls
    assert "post_finalize" in hook.calls


@pytest.mark.asyncio
async def test_component_pool():
    """Test component pool functionality."""
    pool = get_component_pool()
    component1 = TestComponent("test1")
    component2 = TestComponent("test2")

    # Test registration
    pool.register(component1)
    pool.register(component2)
    assert len(pool.get_components()) == 2

    # Test component retrieval
    assert pool.get_component("test1") is component1
    assert pool.get_component("test2") is component2

    # Test bulk operations
    await pool.initialize_all()
    assert all(c.state == LifecycleState.INITIALIZED for c in pool.get_components())

    await pool.start_all()
    assert all(c.state == LifecycleState.RUNNING for c in pool.get_components())

    await pool.stop_all()
    assert all(c.state == LifecycleState.STOPPED for c in pool.get_components())

    await pool.finalize_all()
    assert all(c.state == LifecycleState.FINALIZED for c in pool.get_components())

    # Test error cases
    with pytest.raises(ComponentNotFoundError):
        pool.get_component("nonexistent")

    with pytest.raises(ComponentAlreadyExistsError):
        pool.register(component1)


@pytest.mark.asyncio
async def test_state_monitor():
    """Test state monitor functionality."""
    monitor = get_state_monitor()
    pool = get_component_pool()
    component = TestComponent("test_monitor")
    pool.register(component)

    # Test transition recording
    await component.initialize()
    await component.start()
    await component.stop()
    await component.finalize()

    stats = monitor.get_component_stats("test_monitor")
    assert stats["current_state"] == LifecycleState.FINALIZED
    assert len(stats["transition_counts"]) > 0
    assert stats["error_count"] == 0

    # Test system stats
    sys_stats = monitor.get_system_stats()
    assert sys_stats["total_components"] > 0
    assert "components_by_state" in sys_stats
    assert "total_errors" in sys_stats
