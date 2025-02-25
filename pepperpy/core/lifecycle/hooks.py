"""Lifecycle hooks module.

This module provides standard hooks for lifecycle management.
"""

import logging

from pepperpy.core.lifecycle.types import (
    LifecycleContext,
    LifecycleEvent,
    LifecycleHook,
)
from pepperpy.core.metrics import metrics_manager

logger = logging.getLogger(__name__)


class LoggingHook(LifecycleHook):
    """Hook that logs lifecycle events."""

    async def pre_event(self, context: LifecycleContext) -> None:
        """Log before event.

        Args:
            context: Event context
        """
        logger.info(
            "Starting lifecycle event",
            extra={
                "component_id": context.component_id,
                "event": context.event.value,
                "state": context.state.name,
                "metadata": context.metadata,
            },
        )

    async def post_event(self, context: LifecycleContext) -> None:
        """Log after event.

        Args:
            context: Event context
        """
        logger.info(
            "Completed lifecycle event",
            extra={
                "component_id": context.component_id,
                "event": context.event.value,
                "state": context.state.name,
                "metadata": context.metadata,
            },
        )

    async def on_error(self, context: LifecycleContext) -> None:
        """Log error.

        Args:
            context: Error context
        """
        logger.error(
            "Lifecycle event failed",
            extra={
                "component_id": context.component_id,
                "event": context.event.value,
                "state": context.state.name,
                "error": str(context.error),
                "metadata": context.metadata,
            },
            exc_info=context.error,
        )


class MetricsHook(LifecycleHook):
    """Hook that records metrics for lifecycle events."""

    def __init__(self) -> None:
        """Initialize metrics hook."""
        self._counters = {}
        self._histograms = {}

    async def _ensure_metrics(self, component_id: str) -> None:
        """Ensure metrics exist.

        Args:
            component_id: Component ID
        """
        if component_id not in self._counters:
            self._counters[component_id] = {
                event: await metrics_manager.create_counter(
                    name=f"lifecycle_{event.value}_total",
                    description=f"Total number of {event.value} events",
                )
                for event in LifecycleEvent
            }

        if component_id not in self._histograms:
            self._histograms[component_id] = {
                event: await metrics_manager.create_histogram(
                    name=f"lifecycle_{event.value}_duration_seconds",
                    description=f"Duration of {event.value} events in seconds",
                    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
                )
                for event in LifecycleEvent
            }

    async def pre_event(self, context: LifecycleContext) -> None:
        """Record event start.

        Args:
            context: Event context
        """
        await self._ensure_metrics(context.component_id)
        context.metadata["start_time"] = context.timestamp.timestamp()

    async def post_event(self, context: LifecycleContext) -> None:
        """Record event completion.

        Args:
            context: Event context
        """
        await self._ensure_metrics(context.component_id)
        counter = self._counters[context.component_id][context.event]
        histogram = self._histograms[context.component_id][context.event]

        counter.inc()

        start_time = context.metadata.get("start_time")
        if start_time is not None:
            duration = context.timestamp.timestamp() - start_time
            histogram.observe(duration)

    async def on_error(self, context: LifecycleContext) -> None:
        """Record event error.

        Args:
            context: Error context
        """
        await self._ensure_metrics(context.component_id)
        error_counter = await metrics_manager.create_counter(
            name=f"lifecycle_{context.event.value}_errors_total",
            description=f"Total number of {context.event.value} errors",
        )
        error_counter.inc()
