"""Specialized metric collectors for different subsystems.

This module provides specialized metric collectors for different parts of the system:
- System metrics collectors for hardware and OS-level metrics
- Application metrics collectors for application-specific metrics
- Performance metrics collectors for tracking performance data
- Custom collectors for domain-specific metrics

These collectors extend the base MetricsCollector functionality with specialized
collection, aggregation, and reporting capabilities for different metric types
and sources.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()


class Metric(ABC):
    """Base class for all metrics."""

    def __init__(self, name: str, description: str, metric_type: MetricType):
        """Initialize a metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
            metric_type: The type of metric
        """
        self.name = name
        self.description = description
        self.metric_type = metric_type

    @abstractmethod
    def record(self, value: Any) -> None:
        """Record a value for this metric.

        Args:
            value: The value to record
        """
        pass


class Counter(Metric):
    """A counter metric that can only increase."""

    def __init__(self, name: str, description: str):
        """Initialize a counter metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
        """
        super().__init__(name, description, MetricType.COUNTER)
        self.value = 0

    def record(self, value: int = 1) -> None:
        """Increment the counter.

        Args:
            value: The amount to increment by (default: 1)
        """
        if value < 0:
            raise ValueError("Counter can only be incremented by non-negative values")
        self.value += value

    def get_value(self) -> int:
        """Get the current value of the counter.

        Returns:
            The current value
        """
        return self.value

    def reset(self) -> None:
        """Reset the counter to zero."""
        self.value = 0


class Histogram(Metric):
    """A histogram metric that tracks the distribution of values."""

    def __init__(
        self, name: str, description: str, buckets: Optional[List[float]] = None
    ):
        """Initialize a histogram metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
            buckets: Optional list of bucket boundaries (default: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10])
        """
        super().__init__(name, description, MetricType.HISTOGRAM)
        self.buckets = buckets or [
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1,
            2.5,
            5,
            10,
        ]
        self.counts: Dict[Union[float, str], int] = {
            bucket: 0 for bucket in self.buckets
        }
        self.counts["inf"] = 0
        self.sum = 0
        self.count = 0
        self.min = float("inf")
        self.max = float("-inf")

    def record(self, value: float) -> None:
        """Record a value in the histogram.

        Args:
            value: The value to record
        """
        self.sum += value
        self.count += 1
        self.min = min(self.min, value)
        self.max = max(self.max, value)

        # Increment the appropriate bucket
        for bucket in self.buckets:
            if value <= bucket:
                self.counts[bucket] += 1
                return
        self.counts["inf"] += 1

    def get_buckets(self) -> Dict[Union[float, str], int]:
        """Get the bucket counts.

        Returns:
            Dictionary mapping bucket boundaries to counts
        """
        return self.counts

    def get_sum(self) -> float:
        """Get the sum of all recorded values.

        Returns:
            The sum
        """
        return self.sum

    def get_count(self) -> int:
        """Get the count of recorded values.

        Returns:
            The count
        """
        return self.count

    def get_average(self) -> float:
        """Get the average of all recorded values.

        Returns:
            The average, or 0 if no values have been recorded
        """
        return self.sum / self.count if self.count > 0 else 0

    def get_min(self) -> float:
        """Get the minimum recorded value.

        Returns:
            The minimum, or positive infinity if no values have been recorded
        """
        return self.min

    def get_max(self) -> float:
        """Get the maximum recorded value.

        Returns:
            The maximum, or negative infinity if no values have been recorded
        """
        return self.max

    def reset(self) -> None:
        """Reset the histogram."""
        self.counts = {bucket: 0 for bucket in self.buckets}
        self.counts["inf"] = 0
        self.sum = 0
        self.count = 0
        self.min = float("inf")
        self.max = float("-inf")


class MetricsCollector:
    """Base class for all metrics collectors."""

    def __init__(self, name: str):
        """Initialize a metrics collector.

        Args:
            name: The name of the collector
        """
        self.name = name
        self.metrics: Dict[str, Metric] = {}

    def register_metric(self, metric: Metric) -> None:
        """Register a metric with this collector.

        Args:
            metric: The metric to register
        """
        self.metrics[metric.name] = metric

    def record(self, metric_name: str, value: Any) -> None:
        """Record a value for a metric.

        Args:
            metric_name: The name of the metric
            value: The value to record
        """
        if metric_name in self.metrics:
            self.metrics[metric_name].record(value)

    def create_counter(self, name: str, description: str) -> Counter:
        """Create and register a counter metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures

        Returns:
            The created counter
        """
        counter = Counter(name, description)
        self.register_metric(counter)
        return counter

    def create_histogram(
        self, name: str, description: str, buckets: Optional[List[float]] = None
    ) -> Histogram:
        """Create and register a histogram metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
            buckets: Optional list of bucket boundaries

        Returns:
            The created histogram
        """
        histogram = Histogram(name, description, buckets)
        self.register_metric(histogram)
        return histogram

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name.

        Args:
            name: The name of the metric

        Returns:
            The metric, or None if not found
        """
        return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics.

        Returns:
            Dictionary mapping metric names to metrics
        """
        return self.metrics.copy()

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()


# Import specialized collectors here as they are implemented
# from .system import SystemMetricsCollector
# from .application import ApplicationMetricsCollector
# from .performance import PerformanceMetricsCollector

# Export public API
__all__ = [
    "Counter",
    "Histogram",
    "Metric",
    "MetricType",
    "MetricsCollector",
    # Add specialized collectors here as they are implemented
    # "SystemMetricsCollector",
    # "ApplicationMetricsCollector",
    # "PerformanceMetricsCollector",
]
