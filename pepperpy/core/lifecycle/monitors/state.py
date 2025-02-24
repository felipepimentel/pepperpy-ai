"""
State monitor for tracking lifecycle states and transitions.
"""

from datetime import datetime
from typing import Any

from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.lifecycle.managers.pool import get_component_pool
from pepperpy.core.lifecycle.types import LifecycleState, StateTransition
from pepperpy.core.metrics.unified import MetricsManager


class StateMonitor:
    """Monitors and tracks lifecycle states and transitions."""

    _instance = None

    def __new__(cls) -> "StateMonitor":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._metrics = MetricsManager.get_instance()
            self._state_durations: dict[str, dict[LifecycleState, float]] = {}
            self._transition_counts: dict[str, dict[str, int]] = {}
            self._error_counts: dict[str, int] = {}
            self._last_check: datetime | None = None

    def record_transition(
        self, component: LifecycleComponent, transition: StateTransition
    ) -> None:
        """Record a state transition."""
        # Initialize component tracking if needed
        if component.name not in self._state_durations:
            self._state_durations[component.name] = {
                state: 0.0 for state in LifecycleState
            }
            self._transition_counts[component.name] = {}
            self._error_counts[component.name] = 0

        # Record transition count
        transition_key = f"{transition.from_state}->{transition.to_state}"
        self._transition_counts[component.name][transition_key] = (
            self._transition_counts[component.name].get(transition_key, 0) + 1
        )

        # Record metrics
        self._metrics.record_metric(
            "state_transition",
            1,
            {
                "component": component.name,
                "from_state": str(transition.from_state),
                "to_state": str(transition.to_state),
            },
        )

        # Record error if applicable
        if transition.to_state == LifecycleState.ERROR:
            self._error_counts[component.name] += 1
            self._metrics.record_metric(
                "lifecycle_error", 1, {"component": component.name}
            )

    def update_state_durations(self) -> None:
        """Update state durations for all components."""
        now = datetime.utcnow()
        if self._last_check is None:
            self._last_check = now
            return

        duration = (now - self._last_check).total_seconds()
        pool = get_component_pool()

        for component in pool.get_components():
            if component.name not in self._state_durations:
                self._state_durations[component.name] = {
                    state: 0.0 for state in LifecycleState
                }

            self._state_durations[component.name][component.state] += duration

            # Record state duration metric
            self._metrics.record_metric(
                "state_duration",
                duration,
                {
                    "component": component.name,
                    "state": str(component.state),
                },
            )

        self._last_check = now

    def get_state_durations(self, component_name: str) -> dict[LifecycleState, float]:
        """Get state durations for a component."""
        return self._state_durations.get(component_name, {}).copy()

    def get_transition_counts(self, component_name: str) -> dict[str, int]:
        """Get transition counts for a component."""
        return self._transition_counts.get(component_name, {}).copy()

    def get_error_count(self, component_name: str) -> int:
        """Get error count for a component."""
        return self._error_counts.get(component_name, 0)

    def get_component_stats(self, component_name: str) -> dict[str, Any]:
        """Get comprehensive statistics for a component."""
        return {
            "state_durations": self.get_state_durations(component_name),
            "transition_counts": self.get_transition_counts(component_name),
            "error_count": self.get_error_count(component_name),
            "current_state": get_component_pool().get_component(component_name).state,
        }

    def get_system_stats(self) -> dict[str, Any]:
        """Get system-wide lifecycle statistics."""
        pool = get_component_pool()
        components = pool.get_components()

        return {
            "total_components": len(components),
            "components_by_state": {
                state.value: len(pool.get_components_by_state(state))
                for state in LifecycleState
            },
            "total_errors": sum(self._error_counts.values()),
            "components": {
                component.name: self.get_component_stats(component.name)
                for component in components
            },
        }


def get_state_monitor() -> StateMonitor:
    """Get the global StateMonitor instance."""
    return StateMonitor()
