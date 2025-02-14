"""Type definitions for metrics."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class Metric:
    """Base class for all metrics.

    This class represents a single metric with labels and metadata.

    Attributes:
        name: Metric name
        type: Metric type
        description: Metric description
        labels: Metric labels
        metadata: Additional metadata

    """

    name: str
    type: MetricType
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Counter(Metric):
    """A counter metric.

    This metric can only increase or be reset to zero.

    Attributes:
        value: Current counter value

    """

    value: float = 0.0

    def __post_init__(self) -> None:
        """Initialize counter type."""
        self.type = MetricType.COUNTER

    def inc(self, amount: float = 1.0) -> None:
        """Increment the counter.

        Args:
            amount: Amount to increment by (must be positive)

        Raises:
            ValueError: If amount is negative

        """
        if amount < 0:
            raise ValueError("Counter cannot decrease")
        self.value += amount

    def reset(self) -> None:
        """Reset the counter to zero."""
        self.value = 0.0


@dataclass
class Gauge(Metric):
    """A gauge metric.

    This metric can increase and decrease.

    Attributes:
        value: Current gauge value

    """

    value: float = 0.0

    def __post_init__(self) -> None:
        """Initialize gauge type."""
        self.type = MetricType.GAUGE

    def set(self, value: float) -> None:
        """Set the gauge value.

        Args:
            value: New value

        """
        self.value = value

    def inc(self, amount: float = 1.0) -> None:
        """Increment the gauge.

        Args:
            amount: Amount to increment by

        """
        self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        """Decrement the gauge.

        Args:
            amount: Amount to decrement by

        """
        self.value -= amount


@dataclass
class Histogram(Metric):
    """A histogram metric.

    This metric tracks value distributions.

    Attributes:
        buckets: Histogram buckets
        sum: Sum of all values
        count: Count of all values

    """

    buckets: List[float] = field(default_factory=list)
    sum: float = 0.0
    count: int = 0

    def __post_init__(self) -> None:
        """Initialize histogram type."""
        self.type = MetricType.HISTOGRAM
        if not self.buckets:
            self.buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]

    def observe(self, value: float) -> None:
        """Record a value.

        Args:
            value: Value to record

        """
        self.sum += value
        self.count += 1
