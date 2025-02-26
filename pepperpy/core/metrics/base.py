"""
Core metrics module defining metrics functionality.

This module provides base classes and utilities for implementing metrics
throughout PepperPy.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class MetricValue:
    """Base class for metric values."""

    def __init__(self, value: Any):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class MetricLabels:
    """Container for metric labels."""

    def __init__(self, **labels: str):
        self._labels = labels

    def __str__(self) -> str:
        return str(self._labels)

    def to_dict(self) -> Dict[str, str]:
        """Convert labels to dictionary."""
        return self._labels.copy()


class MetricCounter:
    """Counter metric type."""

    def __init__(
        self, name: str, description: str = "", labels: Optional[MetricLabels] = None
    ):
        self.id = uuid4()
        self.name = name
        self.description = description
        self.labels = labels or MetricLabels()
        self._value = 0

    def increment(self, amount: int = 1) -> None:
        """Increment the counter."""
        self._value += amount

    @property
    def value(self) -> int:
        """Get the current value."""
        return self._value


class MetricHistogram:
    """Histogram metric type."""

    def __init__(
        self,
        name: str,
        buckets: List[float],
        description: str = "",
        labels: Optional[MetricLabels] = None,
    ):
        self.id = uuid4()
        self.name = name
        self.description = description
        self.labels = labels or MetricLabels()
        self.buckets = sorted(buckets)
        self._counts = {b: 0 for b in buckets}
        self._sum = 0.0
        self._count = 0

    def observe(self, value: float) -> None:
        """Record an observation."""
        self._sum += value
        self._count += 1

        for bucket in self.buckets:
            if value <= bucket:
                self._counts[bucket] += 1

    @property
    def counts(self) -> Dict[float, int]:
        """Get the current bucket counts."""
        return self._counts.copy()

    @property
    def sum(self) -> float:
        """Get the sum of all observations."""
        return self._sum

    @property
    def count(self) -> int:
        """Get the total number of observations."""
        return self._count


class MetricsManager:
    """Manager for metrics collection and reporting."""

    def __init__(self):
        self._counters: Dict[UUID, MetricCounter] = {}
        self._histograms: Dict[UUID, MetricHistogram] = {}

    def create_counter(
        self, name: str, description: str = "", labels: Optional[MetricLabels] = None
    ) -> MetricCounter:
        """Create a new counter metric."""
        counter = MetricCounter(name, description, labels)
        self._counters[counter.id] = counter
        return counter

    def create_histogram(
        self,
        name: str,
        buckets: List[float],
        description: str = "",
        labels: Optional[MetricLabels] = None,
    ) -> MetricHistogram:
        """Create a new histogram metric."""
        histogram = MetricHistogram(name, buckets, description, labels)
        self._histograms[histogram.id] = histogram
        return histogram

    def get_counter(self, counter_id: UUID) -> Optional[MetricCounter]:
        """Get a counter by ID."""
        return self._counters.get(counter_id)

    def get_histogram(self, histogram_id: UUID) -> Optional[MetricHistogram]:
        """Get a histogram by ID."""
        return self._histograms.get(histogram_id)

    def collect(self) -> Dict[str, Any]:
        """Collect all metric values."""
        metrics = {}

        for counter in self._counters.values():
            metrics[counter.name] = {
                "type": "counter",
                "value": counter.value,
                "labels": counter.labels.to_dict(),
            }

        for histogram in self._histograms.values():
            metrics[histogram.name] = {
                "type": "histogram",
                "counts": histogram.counts,
                "sum": histogram.sum,
                "count": histogram.count,
                "labels": histogram.labels.to_dict(),
            }

        return metrics


# Export all types
__all__ = [
    "MetricValue",
    "MetricLabels",
    "MetricCounter",
    "MetricHistogram",
    "MetricsManager",
]
