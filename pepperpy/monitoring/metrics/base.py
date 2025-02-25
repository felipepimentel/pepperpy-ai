"""Base metrics module.

This module provides base metrics functionality for monitoring.
"""

from typing import Dict, List, Optional, Union

from pepperpy.core.metrics.types import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    MetricType,
    MetricValue,
    MetricLabels,
)


class MetricsManager:
    """Manager for collecting and exposing metrics."""

    def __init__(self):
        """Initialize the metrics manager."""
        self._metrics: Dict[str, Union[Counter, Gauge, Histogram, Summary]] = {}

    def counter(
        self, name: str, description: str, labels: Optional[List[str]] = None
    ) -> Counter:
        """Create or get a counter metric.

        Args:
            name: Name of the metric
            description: Description of the metric
            labels: Optional list of label names

        Returns:
            Counter metric instance
        """
        key = f"counter_{name}"
        if key not in self._metrics:
            self._metrics[key] = Counter(name, description, labels)
        metric = self._metrics[key]
        if not isinstance(metric, Counter):
            raise TypeError(f"Metric {name} is not a counter")
        return metric

    def gauge(
        self, name: str, description: str, labels: Optional[List[str]] = None
    ) -> Gauge:
        """Create or get a gauge metric.

        Args:
            name: Name of the metric
            description: Description of the metric
            labels: Optional list of label names

        Returns:
            Gauge metric instance
        """
        key = f"gauge_{name}"
        if key not in self._metrics:
            self._metrics[key] = Gauge(name, description, labels)
        metric = self._metrics[key]
        if not isinstance(metric, Gauge):
            raise TypeError(f"Metric {name} is not a gauge")
        return metric

    def histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> Histogram:
        """Create or get a histogram metric.

        Args:
            name: Name of the metric
            description: Description of the metric
            labels: Optional list of label names
            buckets: Optional bucket boundaries

        Returns:
            Histogram metric instance
        """
        key = f"histogram_{name}"
        if key not in self._metrics:
            self._metrics[key] = Histogram(name, description, labels, buckets)
        metric = self._metrics[key]
        if not isinstance(metric, Histogram):
            raise TypeError(f"Metric {name} is not a histogram")
        return metric

    def summary(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        quantiles: Optional[List[float]] = None,
    ) -> Summary:
        """Create or get a summary metric.

        Args:
            name: Name of the metric
            description: Description of the metric
            labels: Optional list of label names
            quantiles: Optional quantiles to track

        Returns:
            Summary metric instance
        """
        key = f"summary_{name}"
        if key not in self._metrics:
            self._metrics[key] = Summary(name, description, labels, quantiles)
        metric = self._metrics[key]
        if not isinstance(metric, Summary):
            raise TypeError(f"Metric {name} is not a summary")
        return metric

    def get_metric(
        self, name: str
    ) -> Union[Counter, Gauge, Histogram, Summary]:
        """Get a metric by name.

        Args:
            name: Name of the metric

        Returns:
            Metric instance

        Raises:
            KeyError: If metric not found
        """
        for key, metric in self._metrics.items():
            if key.endswith(name):
                return metric
        raise KeyError(f"Metric {name} not found")

    def get_all_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram, Summary]]:
        """Get all registered metrics.

        Returns:
            Dictionary mapping metric names to instances
        """
        return self._metrics.copy()


__all__ = ["MetricsManager"]
