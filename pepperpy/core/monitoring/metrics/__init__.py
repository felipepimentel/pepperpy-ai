"""Metrics module for collecting and reporting metrics."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .errors import MetricsError
from .manager import MetricsManager, metrics_manager

__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "Metric",
    "MetricType",
    "MetricValue",
    "MetricsError",
    "MetricsManager",
    "metrics_manager",
]


class MetricType(Enum):
    """Types of metrics supported by the system."""

    COUNTER = "counter"  # Monotonically increasing value
    GAUGE = "gauge"  # Value that can go up and down
    HISTOGRAM = "histogram"  # Distribution of values


@dataclass
class MetricValue:
    """Value of a metric with metadata."""

    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class Metric(ABC):
    """Base class for all metrics."""

    def __init__(
        self,
        name: str,
        description: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize metric.

        Args:
            name: Metric name
            description: Metric description
            tags: Optional metric tags

        """
        self.name = name
        self.description = description
        self.tags = tags or {}
        self._values: List[MetricValue] = []

    @property
    @abstractmethod
    def type(self) -> MetricType:
        """Get metric type."""
        pass

    @property
    def values(self) -> List[MetricValue]:
        """Get metric values."""
        return self._values

    def add_value(
        self, value: float, timestamp: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Add a value to the metric.

        Args:
            value: Metric value
            timestamp: Value timestamp
            tags: Optional value-specific tags

        """
        self._values.append(
            MetricValue(
                value=value,
                timestamp=timestamp,
                tags={**self.tags, **(tags or {})},
            )
        )

    def clear(self) -> None:
        """Clear all values."""
        self._values.clear()


class Counter(Metric):
    """Counter metric that only increases."""

    def __init__(
        self,
        name: str,
        description: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize counter.

        Args:
            name: Counter name
            description: Counter description
            tags: Optional counter tags

        """
        super().__init__(name, description, tags)
        self._value = 0.0

    @property
    def type(self) -> MetricType:
        """Get metric type."""
        return MetricType.COUNTER

    def increment(
        self,
        value: float = 1.0,
        timestamp: float = 0.0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment counter.

        Args:
            value: Value to increment by
            timestamp: Value timestamp
            tags: Optional value-specific tags

        """
        if value < 0:
            raise ValueError("Counter can only be incremented by positive values")
        self._value += value
        self.add_value(self._value, timestamp, tags)


class Gauge(Metric):
    """Gauge metric that can go up and down."""

    def __init__(
        self,
        name: str,
        description: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize gauge.

        Args:
            name: Gauge name
            description: Gauge description
            tags: Optional gauge tags

        """
        super().__init__(name, description, tags)
        self._value = 0.0

    @property
    def type(self) -> MetricType:
        """Get metric type."""
        return MetricType.GAUGE

    def set(
        self,
        value: float,
        timestamp: float = 0.0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set gauge value.

        Args:
            value: New value
            timestamp: Value timestamp
            tags: Optional value-specific tags

        """
        self._value = value
        self.add_value(value, timestamp, tags)

    def increment(
        self,
        value: float = 1.0,
        timestamp: float = 0.0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment gauge.

        Args:
            value: Value to increment by
            timestamp: Value timestamp
            tags: Optional value-specific tags

        """
        self._value += value
        self.add_value(self._value, timestamp, tags)

    def decrement(
        self,
        value: float = 1.0,
        timestamp: float = 0.0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Decrement gauge.

        Args:
            value: Value to decrement by
            timestamp: Value timestamp
            tags: Optional value-specific tags

        """
        self._value -= value
        self.add_value(self._value, timestamp, tags)


class Histogram(Metric):
    """Histogram metric for tracking value distributions."""

    def __init__(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize histogram.

        Args:
            name: Histogram name
            description: Histogram description
            buckets: Optional bucket boundaries
            tags: Optional histogram tags

        """
        super().__init__(name, description, tags)
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
        self._count = 0
        self._sum = 0.0
        self._bucket_counts = dict.fromkeys(self.buckets, 0)

    @property
    def type(self) -> MetricType:
        """Get metric type."""
        return MetricType.HISTOGRAM

    def observe(
        self,
        value: float,
        timestamp: float = 0.0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record an observation.

        Args:
            value: Observed value
            timestamp: Value timestamp
            tags: Optional value-specific tags

        """
        self._count += 1
        self._sum += value
        for bucket in self.buckets:
            if value <= bucket:
                self._bucket_counts[bucket] += 1
        self.add_value(value, timestamp, tags)
