"""Lifecycle hooks module.

This module provides standard hooks for lifecycle management.
"""

import logging
from typing import Any

from pepperpy.core.metrics import Counter, Histogram
from pepperpy.core.protocols.lifecycle import LifecycleHook

logger = logging.getLogger(__name__)


class LoggingHook(LifecycleHook):
    """Hook that logs lifecycle events."""

    def on_start(self, component_id: str, event: str, **kwargs: Any) -> None:
        """Log start of lifecycle event.

        Args:
            component_id: Component identifier
            event: Event name
            **kwargs: Additional event data
        """
        logger.info(f"{component_id}: Starting {event}")

    def on_complete(self, component_id: str, event: str, **kwargs: Any) -> None:
        """Log completion of lifecycle event.

        Args:
            component_id: Component identifier
            event: Event name
            **kwargs: Additional event data
        """
        logger.info(f"{component_id}: Completed {event}")

    def on_error(
        self, component_id: str, event: str, error: Exception, **kwargs: Any
    ) -> None:
        """Log error in lifecycle event.

        Args:
            component_id: Component identifier
            event: Event name
            error: Error that occurred
            **kwargs: Additional event data
        """
        logger.error(f"{component_id}: Error in {event}: {error}")


class MetricsHook(LifecycleHook):
    """Hook that records metrics for lifecycle events."""

    def __init__(self) -> None:
        """Initialize metrics hook."""
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}

    def _ensure_metrics(self, component_id: str, event: str) -> None:
        """Ensure metrics exist for component and event.

        Args:
            component_id: Component identifier
            event: Event name
        """
        counter_key = f"{component_id}_{event}"
        if counter_key not in self._counters:
            self._counters[counter_key] = Counter(
                name="lifecycle_events_total",
                description="Total number of lifecycle events",
                labels=["component_id", "event", "state"],
            )

        histogram_key = f"{component_id}_{event}"
        if histogram_key not in self._histograms:
            self._histograms[histogram_key] = Histogram(
                name="lifecycle_event_duration_seconds",
                description="Duration of lifecycle events",
                labels=["component_id", "event"],
            )

    def on_start(self, component_id: str, event: str, **kwargs: Any) -> None:
        """Record start of lifecycle event.

        Args:
            component_id: Component identifier
            event: Event name
            **kwargs: Additional event data
        """
        self._ensure_metrics(component_id, event)
        counter_key = f"{component_id}_{event}"
        self._counters[counter_key].inc(
            labels={"component_id": component_id, "event": event, "state": "start"}
        )

    def on_complete(
        self,
        component_id: str,
        event: str,
        duration: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Record completion of lifecycle event.

        Args:
            component_id: Component identifier
            event: Event name
            duration: Optional duration of event
            **kwargs: Additional event data
        """
        self._ensure_metrics(component_id, event)
        counter_key = f"{component_id}_{event}"
        histogram_key = f"{component_id}_{event}"

        self._counters[counter_key].inc(
            labels={"component_id": component_id, "event": event, "state": "complete"}
        )

        if duration is not None:
            self._histograms[histogram_key].observe(
                duration, labels={"component_id": component_id, "event": event}
            )

    def on_error(
        self, component_id: str, event: str, error: Exception, **kwargs: Any
    ) -> None:
        """Record error in lifecycle event.

        Args:
            component_id: Component identifier
            event: Event name
            error: Error that occurred
            **kwargs: Additional event data
        """
        self._ensure_metrics(component_id, event)
        counter_key = f"{component_id}_{event}"
        self._counters[counter_key].inc(
            labels={
                "component_id": component_id,
                "event": event,
                "state": "error",
                "error": str(error),
            }
        )
