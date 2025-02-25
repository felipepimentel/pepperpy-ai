"""Core metrics types.

This module defines the core types used for metrics and monitoring.
"""

from enum import Enum, auto
from typing import TypedDict


class MetricLabels(TypedDict, total=False):
    """Type definition for metric labels."""

    service: str
    instance: str
    endpoint: str
    method: str
    status: str
    error: str
    version: str


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()


class MetricValue:
    """Value of a metric."""

    def __init__(
        self,
        value: float,
        type: MetricType,
        labels: MetricLabels | None = None,
    ) -> None:
        """Initialize metric value.

        Args:
            value: Metric value
            type: Metric type
            labels: Optional metric labels
        """
        self.value = value
        self.type = type
        self.labels = labels or {}


class MetricCounter:
    """Counter metric type."""

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: MetricLabels | None = None,
    ) -> None:
        """Initialize counter.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels
        """
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.value = 0.0

    def inc(self, value: float = 1.0) -> None:
        """Increment counter.

        Args:
            value: Value to increment by
        """
        self.value += value


class MetricGauge:
    """Gauge metric type."""

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: MetricLabels | None = None,
    ) -> None:
        """Initialize gauge.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels
        """
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.value = 0.0

    def set(self, value: float) -> None:
        """Set gauge value.

        Args:
            value: Value to set
        """
        self.value = value

    def inc(self, value: float = 1.0) -> None:
        """Increment gauge.

        Args:
            value: Value to increment by
        """
        self.value += value

    def dec(self, value: float = 1.0) -> None:
        """Decrement gauge.

        Args:
            value: Value to decrement by
        """
        self.value -= value


class MetricHistogram:
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
            name: Metric name
            description: Metric description
            buckets: Optional bucket boundaries
            labels: Optional metric labels
        """
        self.name = name
        self.description = description
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.0, 5.0]
        self.labels = labels or {}
        self.values: list[float] = []

    def observe(self, value: float) -> None:
        """Record observation.

        Args:
            value: Value to record
        """
        self.values.append(value)


class MetricSummary:
    """Summary metric type."""

    def __init__(
        self,
        name: str,
        description: str = "",
        quantiles: list[float] | None = None,
        labels: MetricLabels | None = None,
    ) -> None:
        """Initialize summary.

        Args:
            name: Metric name
            description: Metric description
            quantiles: Optional quantiles to track
            labels: Optional metric labels
        """
        self.name = name
        self.description = description
        self.quantiles = quantiles or [0.5, 0.9, 0.99]
        self.labels = labels or {}
        self.values: list[float] = []

    def observe(self, value: float) -> None:
        """Record observation.

        Args:
            value: Value to record
        """
        self.values.append(value)
