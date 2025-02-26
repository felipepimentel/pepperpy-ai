"""Core metrics module.

This module provides the core metrics functionality, including the metrics
manager and base metric types.
"""

from typing import Any, Optional, Union

from pepperpy.core.metrics.types import (
    MetricCounter,
    MetricGauge,
    MetricHistogram,
    MetricLabels,
    MetricType,
    MetricValue,
)
from pepperpy.utils.imports import lazy_import

# Import prometheus_client safely
prometheus_client = lazy_import("prometheus_client")

# Use prometheus_client if available, otherwise use core metrics
if prometheus_client:
    Counter = prometheus_client.Counter
    Gauge = prometheus_client.Gauge
    Histogram = prometheus_client.Histogram
else:
    Counter = MetricCounter
    Gauge = MetricGauge
    Histogram = MetricHistogram


class MetricsManager:
    """Manager for metrics collection and monitoring."""

    def __init__(self):
        """Initialize metrics manager."""
        self._metrics: dict[str, Any] = {}

    def counter(
        self, name: str, description: str, labels: list[str] | None = None
    ) -> Counter | MetricCounter:
        """Create or get a counter metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names

        Returns:
            Counter metric
        """
        key = f"counter_{name}"
        if key not in self._metrics:
            self._metrics[key] = Counter(name, description, labels or [])
        return self._metrics[key]

    def gauge(
        self, name: str, description: str, labels: list[str] | None = None
    ) -> Gauge | MetricGauge:
        """Create or get a gauge metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names

        Returns:
            Gauge metric
        """
        key = f"gauge_{name}"
        if key not in self._metrics:
            self._metrics[key] = Gauge(name, description, labels or [])
        return self._metrics[key]

    def histogram(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
        buckets: list[float] | None = None,
    ) -> Histogram | MetricHistogram:
        """Create or get a histogram metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names
            buckets: Optional bucket boundaries

        Returns:
            Histogram metric
        """
        key = f"histogram_{name}"
        if key not in self._metrics:
            self._metrics[key] = Histogram(
                name, description, labels or [], buckets=buckets
            )
        return self._metrics[key]

    def get_metric(self, name: str) -> Any:
        """Get a metric by name.

        Args:
            name: Metric name

        Returns:
            The metric instance

        Raises:
            KeyError: If metric not found
        """
        for key, metric in self._metrics.items():
            if key.endswith(name):
                return metric
        raise KeyError(f"Metric {name} not found")

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all registered metrics.

        Returns:
            Dictionary mapping metric names to instances
        """
        return self._metrics.copy()


# Global metrics manager instance
metrics_manager = MetricsManager()


__all__ = [
    "MetricLabels",
    "MetricType",
    "MetricValue",
    "MetricsManager",
    "metrics_manager",
]
