"""Type definitions for the metrics module.

This module provides type definitions used throughout the metrics system.
It is designed to be self-contained to avoid circular dependencies.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Any


class MetricType(Enum):
    """Metric types."""

    COUNTER = auto()
    HISTOGRAM = auto()


# Type aliases
MetricLabels = dict[str, str]
MetricValue = dict[str, Any]


class BaseMetric:
    """Base class for all metrics."""

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: MetricLabels | None = None,
    ) -> None:
        """Initialize metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels
        """
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.type: MetricType
        self.value: float = 0.0


class MetricCounter(BaseMetric):
    """Counter metric type."""

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: MetricLabels | None = None,
    ) -> None:
        """Initialize counter.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional counter labels
        """
        super().__init__(name, description, labels)
        self.type = MetricType.COUNTER

    def inc(self, value: float = 1.0) -> None:
        """Increment counter.

        Args:
            value: Value to increment by
        """
        self.value += value


class MetricHistogram(BaseMetric):
    """Histogram metric type."""

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: list[float] | None = None,
        labels: MetricLabels | None = None,
    ) -> None:
        """Initialize histogram.

        Args:
            name: Histogram name
            description: Histogram description
            buckets: Optional histogram buckets
            labels: Optional histogram labels
        """
        super().__init__(name, description, labels)
        self.type = MetricType.HISTOGRAM
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.0, 5.0]
        self._bucket_values = {b: 0 for b in self.buckets}

    def observe(self, value: float) -> None:
        """Observe value.

        Args:
            value: Value to observe
        """
        self.value = value
        for bucket in self.buckets:
            if value <= bucket:
                self._bucket_values[bucket] += 1

    def get_bucket_values(self) -> dict[float, int]:
        """Get bucket values.

        Returns:
            dict[float, int]: Bucket values
        """
        return self._bucket_values.copy()


__all__ = [
    "BaseMetric",
    "MetricCounter",
    "MetricHistogram",
    "MetricLabels",
    "MetricType",
    "MetricValue",
]
