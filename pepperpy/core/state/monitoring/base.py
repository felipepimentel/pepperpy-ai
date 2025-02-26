"""Base monitoring system for state transitions.

This module provides monitoring capabilities for state transitions,
including event tracking, hooks, and metrics collection.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..types import State


@dataclass
class MonitoringEvent:
    """Represents a monitoring event.

    Args:
        event_type (str): Type of event (e.g., "transition", "validation").
        state (State): The state associated with the event.
        timestamp (float): Unix timestamp of the event.
        metadata (Optional[Dict[str, Any]]): Additional event metadata.

    Example:
        >>> event = MonitoringEvent(
        ...     event_type="transition",
        ...     state=State.READY,
        ...     timestamp=datetime.now().timestamp(),
        ...     metadata={"duration": 0.5}
        ... )
    """

    event_type: str
    state: State
    timestamp: float
    metadata: dict[str, Any] | None = None


class StateMonitor:
    """Base class for state transition monitors.

    Example:
        >>> class MyMonitor(StateMonitor):
        ...     def record_transition(self, from_state, to_state):
        ...         print(f"Transition: {from_state} -> {to_state}")
    """

    def record_transition(
        self, from_state: State, to_state: State, metadata: dict[str, Any] | None = None
    ) -> None:
        """Record a state transition.

        Args:
            from_state (State): The starting state.
            to_state (State): The target state.
            metadata (Optional[Dict[str, Any]]): Additional metadata.
        """
        pass

    def record_validation(
        self, state: State, success: bool, error: str | None = None
    ) -> None:
        """Record a validation event.

        Args:
            state (State): The state being validated.
            success (bool): Whether validation succeeded.
            error (Optional[str]): Error message if validation failed.
        """
        pass

    def record_hook(
        self, hook_type: str, state: State, success: bool, error: str | None = None
    ) -> None:
        """Record a hook execution.

        Args:
            hook_type (str): Type of hook ("pre" or "post").
            state (State): The state during hook execution.
            success (bool): Whether hook succeeded.
            error (Optional[str]): Error message if hook failed.
        """
        pass


class MonitoringSystem:
    """System for monitoring state transitions and collecting metrics.

    Example:
        >>> system = MonitoringSystem()
        >>> system.add_monitor(MetricsMonitor())
        >>> system.add_monitor(LoggingMonitor())
        >>> system.record_transition(State.REGISTERED, State.READY)
    """

    def __init__(self):
        """Initialize the monitoring system."""
        self.monitors: list[StateMonitor] = []
        self.events: list[MonitoringEvent] = []

    def add_monitor(self, monitor: StateMonitor) -> None:
        """Add a monitor to the system.

        Args:
            monitor (StateMonitor): The monitor to add.

        Example:
            >>> system = MonitoringSystem()
            >>> system.add_monitor(MetricsMonitor())
        """
        self.monitors.append(monitor)

    def record_transition(
        self, from_state: State, to_state: State, metadata: dict[str, Any] | None = None
    ) -> None:
        """Record a state transition.

        Args:
            from_state (State): The starting state.
            to_state (State): The target state.
            metadata (Optional[Dict[str, Any]]): Additional metadata.

        Example:
            >>> system = MonitoringSystem()
            >>> system.record_transition(
            ...     State.REGISTERED,
            ...     State.READY,
            ...     {"duration": 0.5}
            ... )
        """
        event = MonitoringEvent(
            event_type="transition",
            state=to_state,
            timestamp=datetime.now().timestamp(),
            metadata={
                "from_state": from_state.name,
                "to_state": to_state.name,
                **(metadata or {}),
            },
        )
        self.events.append(event)

        for monitor in self.monitors:
            monitor.record_transition(from_state, to_state, metadata)

    def record_validation(
        self, state: State, success: bool, error: str | None = None
    ) -> None:
        """Record a validation event.

        Args:
            state (State): The state being validated.
            success (bool): Whether validation succeeded.
            error (Optional[str]): Error message if validation failed.

        Example:
            >>> system = MonitoringSystem()
            >>> system.record_validation(
            ...     State.READY,
            ...     False,
            ...     "Missing dependencies"
            ... )
        """
        event = MonitoringEvent(
            event_type="validation",
            state=state,
            timestamp=datetime.now().timestamp(),
            metadata={"success": success, "error": error},
        )
        self.events.append(event)

        for monitor in self.monitors:
            monitor.record_validation(state, success, error)

    def record_hook(
        self, hook_type: str, state: State, success: bool, error: str | None = None
    ) -> None:
        """Record a hook execution.

        Args:
            hook_type (str): Type of hook ("pre" or "post").
            state (State): The state during hook execution.
            success (bool): Whether hook succeeded.
            error (Optional[str]): Error message if hook failed.

        Example:
            >>> system = MonitoringSystem()
            >>> system.record_hook(
            ...     "pre",
            ...     State.READY,
            ...     True
            ... )
        """
        event = MonitoringEvent(
            event_type="hook",
            state=state,
            timestamp=datetime.now().timestamp(),
            metadata={"hook_type": hook_type, "success": success, "error": error},
        )
        self.events.append(event)

        for monitor in self.monitors:
            monitor.record_hook(hook_type, state, success, error)

    def get_events(
        self, start_time: float | None = None, end_time: float | None = None
    ) -> list[MonitoringEvent]:
        """Get monitoring events within a time range.

        Args:
            start_time (Optional[float]): Start timestamp (inclusive).
            end_time (Optional[float]): End timestamp (inclusive).

        Returns:
            List[MonitoringEvent]: Events within the time range.

        Example:
            >>> system = MonitoringSystem()
            >>> events = system.get_events(
            ...     start_time=datetime.now().timestamp() - 3600,
            ...     end_time=datetime.now().timestamp()
            ... )
        """
        filtered = self.events

        if start_time is not None:
            filtered = [e for e in filtered if e.timestamp >= start_time]

        if end_time is not None:
            filtered = [e for e in filtered if e.timestamp <= end_time]

        return filtered


class MetricsMonitor(StateMonitor):
    """Monitor that collects metrics about state transitions.

    Example:
        >>> monitor = MetricsMonitor()
        >>> monitor.record_transition(State.REGISTERED, State.READY)
        >>> print(monitor.get_metrics())
    """

    def __init__(self):
        """Initialize the metrics monitor."""
        self.transition_counts: dict[str, int] = {}
        self.validation_counts: dict[str, int] = {}
        self.hook_counts: dict[str, int] = {}
        self.errors: dict[str, int] = {}

    def record_transition(
        self, from_state: State, to_state: State, metadata: dict[str, Any] | None = None
    ) -> None:
        """Record a state transition in metrics.

        Args:
            from_state (State): The starting state.
            to_state (State): The target state.
            metadata (Optional[Dict[str, Any]]): Additional metadata.
        """
        key = f"{from_state.name}->{to_state.name}"
        self.transition_counts[key] = self.transition_counts.get(key, 0) + 1

    def record_validation(
        self, state: State, success: bool, error: str | None = None
    ) -> None:
        """Record a validation event in metrics.

        Args:
            state (State): The state being validated.
            success (bool): Whether validation succeeded.
            error (Optional[str]): Error message if validation failed.
        """
        key = f"validation_{state.name}"
        self.validation_counts[key] = self.validation_counts.get(key, 0) + 1

        if not success and error:
            self.errors[error] = self.errors.get(error, 0) + 1

    def record_hook(
        self, hook_type: str, state: State, success: bool, error: str | None = None
    ) -> None:
        """Record a hook execution in metrics.

        Args:
            hook_type (str): Type of hook ("pre" or "post").
            state (State): The state during hook execution.
            success (bool): Whether hook succeeded.
            error (Optional[str]): Error message if hook failed.
        """
        key = f"{hook_type}_hook_{state.name}"
        self.hook_counts[key] = self.hook_counts.get(key, 0) + 1

        if not success and error:
            self.errors[error] = self.errors.get(error, 0) + 1

    def get_metrics(self) -> dict[str, dict[str, int]]:
        """Get collected metrics.

        Returns:
            Dict[str, Dict[str, int]]: Collected metrics by category.

        Example:
            >>> monitor = MetricsMonitor()
            >>> metrics = monitor.get_metrics()
            >>> print(metrics["transitions"])
        """
        return {
            "transitions": self.transition_counts,
            "validations": self.validation_counts,
            "hooks": self.hook_counts,
            "errors": self.errors,
        }


class LoggingMonitor(StateMonitor):
    """Monitor that logs state transitions and events.

    Example:
        >>> monitor = LoggingMonitor()
        >>> monitor.record_transition(State.REGISTERED, State.READY)
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the logging monitor.

        Args:
            logger (Optional[logging.Logger]): Logger to use.
                Defaults to module logger.
        """
        self.logger = logger or logging.getLogger(__name__)

    def record_transition(
        self, from_state: State, to_state: State, metadata: dict[str, Any] | None = None
    ) -> None:
        """Log a state transition.

        Args:
            from_state (State): The starting state.
            to_state (State): The target state.
            metadata (Optional[Dict[str, Any]]): Additional metadata.
        """
        self.logger.info(
            "State transition: %s -> %s%s",
            from_state.name,
            to_state.name,
            f" (metadata: {metadata})" if metadata else "",
        )

    def record_validation(
        self, state: State, success: bool, error: str | None = None
    ) -> None:
        """Log a validation event.

        Args:
            state (State): The state being validated.
            success (bool): Whether validation succeeded.
            error (Optional[str]): Error message if validation failed.
        """
        if success:
            self.logger.info("Validation succeeded for state: %s", state.name)
        else:
            self.logger.error(
                "Validation failed for state %s: %s",
                state.name,
                error or "No error message",
            )

    def record_hook(
        self, hook_type: str, state: State, success: bool, error: str | None = None
    ) -> None:
        """Log a hook execution.

        Args:
            hook_type (str): Type of hook ("pre" or "post").
            state (State): The state during hook execution.
            success (bool): Whether hook succeeded.
            error (Optional[str]): Error message if hook failed.
        """
        if success:
            self.logger.info(
                "%s hook succeeded for state: %s", hook_type.capitalize(), state.name
            )
        else:
            self.logger.error(
                "%s hook failed for state %s: %s",
                hook_type.capitalize(),
                state.name,
                error or "No error message",
            )


__all__ = [
    "LoggingMonitor",
    "MetricsMonitor",
    "MonitoringEvent",
    "MonitoringSystem",
    "StateMonitor",
]
