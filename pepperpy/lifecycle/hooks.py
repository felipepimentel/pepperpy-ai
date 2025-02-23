"""Lifecycle hooks module.

This module provides hooks for lifecycle events.
"""

import logging
from typing import Any

from pepperpy.lifecycle.types import LifecycleContext, LifecycleHook

logger = logging.getLogger(__name__)


class LoggingHook(LifecycleHook):
    """Hook for logging lifecycle events."""

    def __init__(self, log_level: int = logging.INFO) -> None:
        """Initialize logging hook.

        Args:
            log_level: Logging level
        """
        self._log_level = log_level

    def _log(self, event: str, context: LifecycleContext) -> None:
        """Log lifecycle event.

        Args:
            event: Event name
            context: Lifecycle context
        """
        logger.log(
            self._log_level,
            f"Lifecycle event: {event}",
            extra={
                "component_id": context.component_id,
                "state": context.state,
                "event": event,
                "metrics": context.metrics.dict(),
            },
        )

    async def pre_init(self, context: LifecycleContext) -> None:
        """Handle pre-init event.

        Args:
            context: Lifecycle context
        """
        self._log("pre_init", context)

    async def post_init(self, context: LifecycleContext) -> None:
        """Handle post-init event.

        Args:
            context: Lifecycle context
        """
        self._log("post_init", context)

    async def pre_start(self, context: LifecycleContext) -> None:
        """Handle pre-start event.

        Args:
            context: Lifecycle context
        """
        self._log("pre_start", context)

    async def post_start(self, context: LifecycleContext) -> None:
        """Handle post-start event.

        Args:
            context: Lifecycle context
        """
        self._log("post_start", context)

    async def pre_stop(self, context: LifecycleContext) -> None:
        """Handle pre-stop event.

        Args:
            context: Lifecycle context
        """
        self._log("pre_stop", context)

    async def post_stop(self, context: LifecycleContext) -> None:
        """Handle post-stop event.

        Args:
            context: Lifecycle context
        """
        self._log("post_stop", context)

    async def pre_finalize(self, context: LifecycleContext) -> None:
        """Handle pre-finalize event.

        Args:
            context: Lifecycle context
        """
        self._log("pre_finalize", context)

    async def post_finalize(self, context: LifecycleContext) -> None:
        """Handle post-finalize event.

        Args:
            context: Lifecycle context
        """
        self._log("post_finalize", context)

    async def on_error(self, context: LifecycleContext, error: Exception) -> None:
        """Handle error event.

        Args:
            context: Lifecycle context
            error: Error that occurred
        """
        logger.log(
            self._log_level,
            f"Lifecycle error: {error}",
            extra={
                "component_id": context.component_id,
                "state": context.state,
                "event": "error",
                "error": str(error),
                "metrics": context.metrics.dict(),
            },
            exc_info=True,
        )


class MetricsHook(LifecycleHook):
    """Hook for collecting lifecycle metrics."""

    def __init__(self) -> None:
        """Initialize metrics hook."""
        self._metrics: dict[str, dict[str, Any]] = {}

    def get_metrics(self, component_id: str) -> dict[str, Any] | None:
        """Get metrics for component.

        Args:
            component_id: Component ID

        Returns:
            Component metrics or None if not found
        """
        return self._metrics.get(component_id)

    def _update_metrics(self, context: LifecycleContext) -> None:
        """Update component metrics.

        Args:
            context: Lifecycle context
        """
        self._metrics[context.component_id] = context.metrics.dict()

    async def pre_init(self, context: LifecycleContext) -> None:
        """Handle pre-init event.

        Args:
            context: Lifecycle context
        """
        self._update_metrics(context)

    async def post_init(self, context: LifecycleContext) -> None:
        """Handle post-init event.

        Args:
            context: Lifecycle context
        """
        self._update_metrics(context)

    async def pre_start(self, context: LifecycleContext) -> None:
        """Handle pre-start event.

        Args:
            context: Lifecycle context
        """
        self._update_metrics(context)

    async def post_start(self, context: LifecycleContext) -> None:
        """Handle post-start event.

        Args:
            context: Lifecycle context
        """
        self._update_metrics(context)

    async def pre_stop(self, context: LifecycleContext) -> None:
        """Handle pre-stop event.

        Args:
            context: Lifecycle context
        """
        self._update_metrics(context)

    async def post_stop(self, context: LifecycleContext) -> None:
        """Handle post-stop event.

        Args:
            context: Lifecycle context
        """
        self._update_metrics(context)

    async def pre_finalize(self, context: LifecycleContext) -> None:
        """Handle pre-finalize event.

        Args:
            context: Lifecycle context
        """
        self._update_metrics(context)

    async def post_finalize(self, context: LifecycleContext) -> None:
        """Handle post-finalize event.

        Args:
            context: Lifecycle context
        """
        self._update_metrics(context)

    async def on_error(self, context: LifecycleContext, error: Exception) -> None:
        """Handle error event.

        Args:
            context: Lifecycle context
            error: Error that occurred
        """
        self._update_metrics(context)
