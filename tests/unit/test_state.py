"""Unit tests for the state management system.

This module provides comprehensive unit tests for all components
of the state management system.
"""

import pytest

from pepperpy.state import (
    InvalidStateTransitionError,
    MetricsMonitor,
    OrderedStateValidator,
    RequiredStateValidator,
    State,
    StateManager,
    StateMetadata,
    StateValidationError,
    TransitionHooks,
)


@pytest.fixture
def state_manager():
    """Fixture providing a configured state manager."""
    manager = StateManager()
    manager.add_transition(State.UNREGISTERED, State.REGISTERED)
    manager.add_transition(State.REGISTERED, State.READY)
    manager.add_transition(State.READY, State.RUNNING)
    return manager


class TestStateTransitions:
    """Test suite for state transitions."""

    def test_initial_state(self, state_manager):
        """Test initial state is UNREGISTERED."""
        assert state_manager.current_state == State.UNREGISTERED

    def test_valid_transition(self, state_manager):
        """Test valid state transition."""
        state_manager.transition_to(State.REGISTERED)
        assert state_manager.current_state == State.REGISTERED

    def test_invalid_transition(self, state_manager):
        """Test invalid state transition raises error."""
        with pytest.raises(InvalidStateTransitionError):
            state_manager.transition_to(State.RUNNING)

    def test_transition_hooks(self):
        """Test transition hooks execution."""
        hooks_called = []

        def pre_hook(machine):
            hooks_called.append("pre")

        def post_hook(machine):
            hooks_called.append("post")

        manager = StateManager()
        manager.add_transition(
            State.UNREGISTERED,
            State.REGISTERED,
            hooks=TransitionHooks(pre_transition=pre_hook, post_transition=post_hook),
        )

        manager.transition_to(State.REGISTERED)
        assert hooks_called == ["pre", "post"]


class TestStateValidation:
    """Test suite for state validation."""

    def test_required_state_validator(self, state_manager):
        """Test RequiredStateValidator."""
        state_manager.add_validator(
            State.RUNNING, RequiredStateValidator({State.REGISTERED})
        )

        with pytest.raises(StateValidationError):
            state_manager.transition_to(State.RUNNING)

        state_manager.transition_to(State.REGISTERED)
        state_manager.transition_to(State.READY)
        state_manager.transition_to(State.RUNNING)
        assert state_manager.current_state == State.RUNNING

    def test_ordered_state_validator(self, state_manager):
        """Test OrderedStateValidator."""
        state_manager.add_global_validator(
            OrderedStateValidator([State.REGISTERED, State.READY, State.RUNNING])
        )

        with pytest.raises(StateValidationError):
            state_manager.transition_to(State.RUNNING)

        state_manager.transition_to(State.REGISTERED)
        state_manager.transition_to(State.READY)
        state_manager.transition_to(State.RUNNING)
        assert state_manager.current_state == State.RUNNING


class TestStateHistory:
    """Test suite for state history tracking."""

    def test_history_tracking(self, state_manager):
        """Test state history is properly tracked."""
        history = state_manager.get_history()
        assert len(history) == 1
        assert isinstance(history[0], StateMetadata)
        assert "Initial state" in history[0].description

        state_manager.transition_to(State.REGISTERED, {"reason": "test"})
        history = state_manager.get_history()
        assert len(history) == 2
        assert history[1].metadata == {"reason": "test"}

    def test_timestamp_order(self, state_manager):
        """Test timestamps are in ascending order."""
        state_manager.transition_to(State.REGISTERED)
        state_manager.transition_to(State.READY)

        timestamps = [entry.timestamp for entry in state_manager.get_history()]
        assert all(t1 <= t2 for t1, t2 in zip(timestamps, timestamps[1:], strict=False))


class TestStateMetrics:
    """Test suite for state metrics collection."""

    def test_transition_metrics(self, state_manager):
        """Test transition metrics are collected."""
        state_manager.transition_to(State.REGISTERED)
        state_manager.transition_to(State.READY)

        metrics_monitor = next(
            m for m in state_manager.monitor.monitors if isinstance(m, MetricsMonitor)
        )
        metrics = metrics_monitor.get_metrics()

        transitions = metrics["transitions"]
        assert transitions["UNREGISTERED->REGISTERED"] == 1
        assert transitions["REGISTERED->READY"] == 1

    def test_validation_metrics(self, state_manager):
        """Test validation metrics are collected."""
        state_manager.add_validator(
            State.RUNNING,
            RequiredStateValidator({State.PAUSED}),  # Impossible requirement
        )

        try:
            state_manager.transition_to(State.RUNNING)
        except StateValidationError:
            pass

        metrics_monitor = next(
            m for m in state_manager.monitor.monitors if isinstance(m, MetricsMonitor)
        )
        metrics = metrics_monitor.get_metrics()

        validations = metrics["validations"]
        assert validations["validation_RUNNING"] == 1  # Failed validation
        assert len(metrics["errors"]) == 1  # One validation error
