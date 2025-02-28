"""Resource monitoring module.

This module provides monitoring functionality for resources.
"""

import asyncio
from datetime import datetime
from typing import Any

from pepperpy.core.common.base import Lifecycle
from pepperpy.core.errors import ValidationError
from pepperpy.core.common.metrics import Counter, Gauge, Histogram
from pepperpy.core.common.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.resources.types import Resource, ResourceState


class ResourceMonitor(Lifecycle):
    """Resource monitor."""

    def __init__(
        self,
        monitor_interval: int = 60,  # 1 minute
    ) -> None:
        """Initialize resource monitor.

        Args:
            monitor_interval: Monitor interval in seconds
        """
        super().__init__()
        self._monitor_interval = monitor_interval
        self._state = ComponentState.CREATED
        self._resources: dict[str, Resource] = {}
        self._task: asyncio.Task[None] | None = None

        # Initialize metrics
        self._resource_count = Gauge(
            "resources_total",
            "Total number of resources",
        )
        self._resource_states = Counter(
            "resource_states_total",
            "Resource states",
        )
        self._resource_size = Histogram(
            "resource_size_bytes",
            "Resource size in bytes",
        )
        self._resource_age = Histogram(
            "resource_age_seconds",
            "Resource age in seconds",
        )

    async def initialize(self) -> None:
        """Initialize monitor."""
        try:
            self._state = ComponentState.INITIALIZING
            self._task = asyncio.create_task(self._monitor_loop())
            self._state = ComponentState.READY
            logger.info("Resource monitor initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize monitor: {e}")

    async def cleanup(self) -> None:
        """Clean up monitor."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            self._state = ComponentState.CLEANED
            logger.info("Resource monitor cleaned up")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up monitor: {e}")

    def register_resource(self, resource: Resource) -> None:
        """Register resource for monitoring.

        Args:
            resource: Resource to register
        """
        self._resources[resource.id] = resource
        self._resource_count.inc()
        self._resource_states.inc({"state": resource.state})
        self._resource_size.observe(resource.metadata.size)
        logger.debug(f"Registered resource for monitoring: {resource.id}")

    def unregister_resource(self, resource_id: str) -> None:
        """Unregister resource from monitoring.

        Args:
            resource_id: Resource ID
        """
        if resource_id in self._resources:
            resource = self._resources[resource_id]
            del self._resources[resource_id]
            self._resource_count.dec()
            self._resource_states.dec({"state": resource.state})
            logger.debug(f"Unregistered resource from monitoring: {resource_id}")

    async def _monitor_loop(self) -> None:
        """Run monitor loop."""
        while True:
            try:
                await asyncio.sleep(self._monitor_interval)
                await self._collect_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)

    async def _collect_metrics(self) -> None:
        """Collect resource metrics."""
        now = datetime.utcnow()
        state_counts: dict[str, int] = {state.value: 0 for state in ResourceState}

        for resource in self._resources.values():
            # Update state counts
            state_counts[str(resource.state)] += 1

            # Update size metric
            self._resource_size.observe(resource.metadata.size)

            # Update age metric
            age = (now - resource.metadata.created_at).total_seconds()
            self._resource_age.observe(age)

        # Update state metrics
        for state, count in state_counts.items():
            self._resource_states.set({"state": state}, count)

        logger.debug(
            "Resource metrics collected",
            extra={
                "total_resources": len(self._resources),
                "state_counts": state_counts,
            },
        )

    def get_metrics(self) -> dict[str, Any]:
        """Get resource metrics.

        Returns:
            Dictionary containing:
            - total_resources: Total number of resources
            - state_counts: Resource state counts
            - size_stats: Resource size statistics
            - age_stats: Resource age statistics
        """
        now = datetime.utcnow()
        state_counts = {state.value: 0 for state in ResourceState}
        size_stats = {
            "min": float("inf"),
            "max": 0,
            "total": 0,
            "count": 0,
        }
        age_stats = {
            "min": float("inf"),
            "max": 0,
            "total": 0,
            "count": 0,
        }

        for resource in self._resources.values():
            # Update state counts
            state_counts[str(resource.state)] += 1

            # Update size stats
            size = resource.metadata.size
            size_stats["min"] = min(size_stats["min"], size)
            size_stats["max"] = max(size_stats["max"], size)
            size_stats["total"] += size
            size_stats["count"] += 1

            # Update age stats
            age = (now - resource.metadata.created_at).total_seconds()
            age_stats["min"] = min(age_stats["min"], age)
            age_stats["max"] = max(age_stats["max"], age)
            age_stats["total"] += age
            age_stats["count"] += 1

        # Calculate averages
        if size_stats["count"] > 0:
            size_stats["avg"] = size_stats["total"] / size_stats["count"]
        if age_stats["count"] > 0:
            age_stats["avg"] = age_stats["total"] / age_stats["count"]

        return {
            "total_resources": len(self._resources),
            "state_counts": state_counts,
            "size_stats": size_stats,
            "age_stats": age_stats,
        }


# Export public API
__all__ = ["ResourceMonitor"]
