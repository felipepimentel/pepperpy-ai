"""Advanced resource metrics system.

This module provides advanced metrics collection and monitoring for resources:
- Resource usage tracking
- Performance metrics
- Health metrics
- Capacity planning metrics
"""

from dataclasses import dataclass, field
from datetime import datetime

from pepperpy.core.metrics import MetricsCollector
from pepperpy.monitoring import logger
from pepperpy.resources.types import Resource, ResourceState


@dataclass
class ResourceMetrics:
    """Resource metrics container."""

    resource_id: str
    resource_type: str
    metrics: dict[str, float] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ResourceMetricsCollector:
    """Advanced resource metrics collector."""

    def __init__(self) -> None:
        """Initialize the resource metrics collector."""
        self._collector = MetricsCollector()
        self._logger = logger.getChild("metrics")

        # Resource count metrics
        self.total_resources = self._collector.gauge(
            "resources_total", {"description": "Total number of resources"},
        )
        self.active_resources = self._collector.gauge(
            "resources_active", {"description": "Number of active resources"},
        )
        self.failed_resources = self._collector.gauge(
            "resources_failed", {"description": "Number of failed resources"},
        )

        # Resource state metrics
        self.state_transitions = self._collector.counter(
            "resource_state_transitions_total",
            {"description": "Number of resource state transitions"},
        )

        # Resource performance metrics
        self.operation_duration = self._collector.histogram(
            "resource_operation_duration_seconds",
            [0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            {"description": "Duration of resource operations"},
        )
        self.operation_errors = self._collector.counter(
            "resource_operation_errors_total",
            {"description": "Number of resource operation errors"},
        )

        # Resource usage metrics
        self.memory_usage = self._collector.gauge(
            "resource_memory_bytes", {"description": "Resource memory usage in bytes"},
        )
        self.cpu_usage = self._collector.gauge(
            "resource_cpu_percent", {"description": "Resource CPU usage percentage"},
        )
        self.disk_usage = self._collector.gauge(
            "resource_disk_bytes", {"description": "Resource disk usage in bytes"},
        )

        # Resource health metrics
        self.health_score = self._collector.gauge(
            "resource_health_score", {"description": "Resource health score (0-100)"},
        )
        self.last_error_time = self._collector.gauge(
            "resource_last_error_timestamp",
            {"description": "Timestamp of last resource error"},
        )

        # Resource capacity metrics
        self.capacity_used = self._collector.gauge(
            "resource_capacity_used_percent",
            {"description": "Resource capacity usage percentage"},
        )
        self.capacity_available = self._collector.gauge(
            "resource_capacity_available_percent",
            {"description": "Resource capacity available percentage"},
        )

    def track_resource(self, resource: Resource) -> None:
        """Track a resource's metrics.

        Args:
            resource: Resource to track

        """
        try:
            # Update basic metrics
            self.total_resources.inc()
            if resource.state == ResourceState.LOADED:
                self.active_resources.inc()
            elif resource.state == ResourceState.FAILED:
                self.failed_resources.inc()

            # Update resource-specific metrics
            self._update_resource_metrics(resource)

            self._logger.debug(
                f"Updated metrics for resource {resource.id}",
                extra={
                    "resource_id": resource.id,
                    "resource_type": resource.type.value,
                    "state": resource.state.value,
                },
            )

        except Exception as e:
            self._logger.error(
                f"Failed to track resource metrics: {e}",
                extra={"resource_id": resource.id, "error": str(e)},
                exc_info=True,
            )

    def _update_resource_metrics(self, resource: Resource) -> None:
        """Update resource-specific metrics.

        Args:
            resource: Resource to update metrics for

        """
        labels = {"resource_id": resource.id, "resource_type": resource.type.value}

        # Update memory usage if available
        if hasattr(resource, "memory_usage"):
            self.memory_usage.set(resource.memory_usage, labels)

        # Update CPU usage if available
        if hasattr(resource, "cpu_usage"):
            self.cpu_usage.set(resource.cpu_usage, labels)

        # Update disk usage if available
        if hasattr(resource, "disk_usage"):
            self.disk_usage.set(resource.disk_usage, labels)

        # Update health metrics
        health_score = self._calculate_health_score(resource)
        self.health_score.set(health_score, labels)

        # Update capacity metrics
        if hasattr(resource, "capacity_used"):
            self.capacity_used.set(resource.capacity_used, labels)
            self.capacity_available.set(100 - resource.capacity_used, labels)

    def _calculate_health_score(self, resource: Resource) -> float:
        """Calculate resource health score.

        Args:
            resource: Resource to calculate health score for

        Returns:
            Health score between 0 and 100

        """
        # Base score on resource state
        if resource.state == ResourceState.LOADED:
            base_score = 100
        elif resource.state == ResourceState.LOADING:
            base_score = 50
        elif resource.state == ResourceState.FAILED:
            base_score = 0
        else:
            base_score = 25

        # Adjust score based on resource-specific metrics
        adjustments = []

        # Memory usage penalty
        if hasattr(resource, "memory_usage"):
            memory_score = 100 - min(resource.memory_usage, 100)
            adjustments.append(memory_score)

        # CPU usage penalty
        if hasattr(resource, "cpu_usage"):
            cpu_score = 100 - min(resource.cpu_usage, 100)
            adjustments.append(cpu_score)

        # Error history penalty
        if hasattr(resource, "error_count"):
            error_penalty = min(resource.error_count * 10, 50)
            base_score = max(0, base_score - error_penalty)

        # Calculate final score
        if adjustments:
            adjustment_score = sum(adjustments) / len(adjustments)
            final_score = (base_score + adjustment_score) / 2
        else:
            final_score = base_score

        return max(0, min(final_score, 100))

    def record_operation(
        self, resource_id: str, operation: str, duration: float, success: bool = True,
    ) -> None:
        """Record a resource operation.

        Args:
            resource_id: ID of the resource
            operation: Name of the operation
            duration: Duration of the operation in seconds
            success: Whether the operation was successful

        """
        labels = {
            "resource_id": resource_id,
            "operation": operation,
            "success": str(success).lower(),
        }

        self.operation_duration.observe(duration, labels)

        if not success:
            self.operation_errors.inc(labels)
            self.last_error_time.set(datetime.utcnow().timestamp(), labels)

    def get_resource_metrics(self, resource_id: str) -> ResourceMetrics:
        """Get metrics for a specific resource.

        Args:
            resource_id: ID of the resource

        Returns:
            ResourceMetrics object containing all metrics for the resource

        """
        metrics = {}
        labels = {"resource_id": resource_id}

        # Collect all metrics for the resource
        for name, metric in self._collector.get_metrics().items():
            for _key, value in metric.items():
                if (
                    "resource_id" in value.labels
                    and value.labels["resource_id"] == resource_id
                ):
                    metrics[name] = value.value

        return ResourceMetrics(
            resource_id=resource_id,
            resource_type=metrics.get("resource_type", "unknown"),
            metrics=metrics,
            labels=labels,
        )


# Export public API
__all__ = ["ResourceMetrics", "ResourceMetricsCollector"]
