"""Core metrics interfaces and base classes."""

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel, Field

from pepperpy.monitoring.metrics.types import MetricLabels, MetricValue

logger = logging.getLogger(__name__)


class MetricConfig(BaseModel):
    """Configuration for a metric.

    Attributes:
        name: Metric name
        description: Metric description
        unit: Metric unit
        labels: Metric labels
    """

    name: str
    description: str
    unit: str = "count"
    labels: MetricLabels = Field(default_factory=dict)


class MetricPoint(BaseModel):
    """A single metric data point.

    Attributes:
        name: Metric name
        value: Metric value
        timestamp: Unix timestamp
        labels: Metric labels
    """

    name: str
    value: MetricValue
    timestamp: float
    labels: MetricLabels = Field(default_factory=dict)


class BaseMetric(ABC):
    """Base class for all metrics."""

    def __init__(self, config: MetricConfig) -> None:
        """Initialize metric.

        Args:
            config: Metric configuration
        """
        self.name = config.name
        self.description = config.description
        self.unit = config.unit
        self.labels = config.labels

    @abstractmethod
    def record(self, value: MetricValue) -> None:
        """Record a metric value.

        Args:
            value: Value to record
        """
        pass

    @abstractmethod
    def get_points(self) -> List[MetricPoint]:
        """Get all recorded points.

        Returns:
            List of metric points
        """
        pass


class Counter(BaseMetric):
    """Counter metric that only increases."""

    def __init__(self, config: MetricConfig) -> None:
        """Initialize counter.

        Args:
            config: Counter configuration
        """
        super().__init__(config)
        self._value: int = 0
        self._points: List[MetricPoint] = []

    def record(self, value: MetricValue = 1) -> None:
        """Record a counter value.

        Args:
            value: Value to add (must be non-negative)

        Raises:
            ValueError: If value is not numeric or negative
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Counter value must be numeric")
        if value < 0:
            raise ValueError("Counter value must be non-negative")

        self._value += int(value)
        self._points.append(
            MetricPoint(
                name=self.name,
                value=self._value,
                timestamp=time.time(),
                labels=self.labels,
            )
        )

    def get_points(self) -> List[MetricPoint]:
        """Get all recorded points.

        Returns:
            List of metric points
        """
        return self._points.copy()


class Gauge(BaseMetric):
    """Gauge metric that can go up and down."""

    def __init__(self, config: MetricConfig) -> None:
        """Initialize gauge.

        Args:
            config: Gauge configuration
        """
        super().__init__(config)
        self._value: Optional[float] = None
        self._points: List[MetricPoint] = []

    def record(self, value: MetricValue) -> None:
        """Record a gauge value.

        Args:
            value: Value to set

        Raises:
            ValueError: If value is not numeric
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Gauge value must be numeric")

        self._value = float(value)
        self._points.append(
            MetricPoint(
                name=self.name,
                value=self._value,
                timestamp=time.time(),
                labels=self.labels,
            )
        )

    def get_points(self) -> List[MetricPoint]:
        """Get all recorded points.

        Returns:
            List of metric points
        """
        return self._points.copy()


class Histogram(BaseMetric):
    """Histogram metric for measuring distributions."""

    def __init__(self, config: MetricConfig, buckets: List[float]) -> None:
        """Initialize histogram.

        Args:
            config: Histogram configuration
            buckets: Bucket boundaries in ascending order

        Raises:
            ValueError: If buckets are not in ascending order
        """
        super().__init__(config)
        if not all(buckets[i] < buckets[i + 1] for i in range(len(buckets) - 1)):
            raise ValueError("Histogram buckets must be in ascending order")
        self._buckets = buckets
        self._counts = [0] * (len(buckets) + 1)  # +1 for overflow bucket
        self._sum = 0.0
        self._count = 0
        self._points: List[MetricPoint] = []

    def record(self, value: MetricValue) -> None:
        """Record a histogram value.

        Args:
            value: Value to record

        Raises:
            ValueError: If value is not numeric
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Histogram value must be numeric")

        value = float(value)
        self._sum += value
        self._count += 1

        # Find the appropriate bucket
        for i, bucket in enumerate(self._buckets):
            if value <= bucket:
                self._counts[i] += 1
                break
        else:
            # Value is larger than all buckets
            self._counts[-1] += 1

        self._points.append(
            MetricPoint(
                name=self.name,
                value=value,
                timestamp=time.time(),
                labels=self.labels,
            )
        )

    def get_points(self) -> List[MetricPoint]:
        """Get all recorded points.

        Returns:
            List of metric points
        """
        return self._points.copy()

    @property
    def count(self) -> int:
        """Get total count of observations.

        Returns:
            Total count
        """
        return self._count

    @property
    def sum(self) -> float:
        """Get sum of all observations.

        Returns:
            Sum of values
        """
        return self._sum

    @property
    def buckets(self) -> List[float]:
        """Get bucket boundaries.

        Returns:
            List of bucket boundaries
        """
        return self._buckets.copy()

    @property
    def counts(self) -> List[int]:
        """Get bucket counts.

        Returns:
            List of counts for each bucket
        """
        return self._counts.copy()
