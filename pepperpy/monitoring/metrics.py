"""Metrics collection for the Pepperpy framework.

This module provides metrics collection functionality using:
- Counter metrics for monotonically increasing values
- Gauge metrics for values that can go up and down
- Histogram metrics for value distributions
- Summary metrics for statistical summaries
"""

from collections.abc import Callable
from typing import Union

from pepperpy.core.enums import MetricType

__all__ = ["Metrics", "metrics"]

# Type aliases for better readability
MetricValue = Union[int, float]
MetricLabels = dict[str, str]
MetricCallback = Callable[[], MetricValue]


class Metrics:
    """Metrics collector for monitoring system behavior."""

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._metrics: dict[str, tuple[MetricType, MetricValue]] = {}
        self._callbacks: dict[str, tuple[MetricType, MetricCallback]] = {}

    def register_callback(
        self,
        name: str,
        callback: MetricCallback,
        metric_type: MetricType,
    ) -> None:
        """Register a callback for collecting metrics.

        Args:
        ----
            name: Metric name
            callback: Function that returns the metric value
            metric_type: Type of metric to collect

        """
        self._callbacks[name] = (metric_type, callback)

    def record_metric(
        self,
        name: str,
        value: MetricValue,
        metric_type: MetricType,
        labels: MetricLabels | None = None,
    ) -> None:
        """Record a metric value.

        Args:
        ----
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Optional metric labels

        """
        self._metrics[name] = (metric_type, value)

    def get_metric(self, name: str) -> tuple[MetricType, MetricValue] | None:
        """Get a metric value.

        Args:
        ----
            name: Metric name

        Returns:
        -------
            Tuple of metric type and value, or None if not found

        """
        if name in self._metrics:
            return self._metrics[name]
        if name in self._callbacks:
            metric_type, callback = self._callbacks[name]
            value = callback()
            return metric_type, value
        return None

    def clear_metric(self, name: str) -> None:
        """Clear a metric.

        Args:
        ----
            name: Metric name

        """
        self._metrics.pop(name, None)
        self._callbacks.pop(name, None)

    def clear_all(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self._callbacks.clear()


# Create default metrics instance
metrics = Metrics()
