"""@file: types.py
@purpose: Core metrics types
@component: Core > Metrics
@created: 2024-03-21
@task: TASK-007-R060
@status: active
"""

from enum import Enum
from typing import Union

# Type aliases
MetricValue = Union[int, float]
MetricLabels = Union[dict[str, str], list[str], None]


class MetricType(Enum):
    """Types of metrics supported."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricBase:
    """Base class for all metrics."""

    def __init__(
        self,
        name: str,
        description: str,
        labels: MetricLabels = None,
    ) -> None:
        """Initialize the metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels
        """
        self.name = name
        self.description = description
        self.labels = labels or {}
        if isinstance(self.labels, list):
            self.labels = {label: "" for label in self.labels}

    def _get_key(self, labels: dict[str, str] | None = None) -> str:
        """Get the metric key with labels.

        Args:
            labels: Optional label values

        Returns:
            Metric key with labels
        """
        if not labels:
            return self.name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{self.name}{{{label_str}}}"


class MetricCounter(MetricBase):
    """Counter metric type.

    Counters can only increase in value and reset when the process restarts.
    """

    def __init__(
        self,
        name: str,
        description: str,
        labels: MetricLabels = None,
    ) -> None:
        """Initialize the counter.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional counter labels
        """
        super().__init__(name, description, labels)
        self._values: dict[str, float] = {}

    def inc(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Increment the counter.

        Args:
            value: Value to increment by
            labels: Optional label values
        """
        key = self._get_key(labels)
        self._values[key] = self._values.get(key, 0.0) + value

    def get(self, labels: dict[str, str] | None = None) -> float:
        """Get the current counter value.

        Args:
            labels: Optional label values

        Returns:
            Current counter value
        """
        return self._values.get(self._get_key(labels), 0.0)


class MetricGauge(MetricBase):
    """Gauge metric type.

    Gauges can increase and decrease in value.
    """

    def __init__(
        self,
        name: str,
        description: str,
        labels: MetricLabels = None,
    ) -> None:
        """Initialize the gauge.

        Args:
            name: Gauge name
            description: Gauge description
            labels: Optional gauge labels
        """
        super().__init__(name, description, labels)
        self._values: dict[str, float] = {}

    def set(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Set the gauge value.

        Args:
            value: Value to set
            labels: Optional label values
        """
        self._values[self._get_key(labels)] = value

    def inc(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Increment the gauge.

        Args:
            value: Value to increment by
            labels: Optional label values
        """
        key = self._get_key(labels)
        self._values[key] = self._values.get(key, 0.0) + value

    def dec(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Decrement the gauge.

        Args:
            value: Value to decrement by
            labels: Optional label values
        """
        self.inc(-value, labels)

    def get(self, labels: dict[str, str] | None = None) -> float:
        """Get the current gauge value.

        Args:
            labels: Optional label values

        Returns:
            Current gauge value
        """
        return self._values.get(self._get_key(labels), 0.0)


class MetricHistogram(MetricBase):
    """Histogram metric type.

    Histograms track the size and number of events in buckets.
    """

    def __init__(
        self,
        name: str,
        description: str,
        buckets: list[float],
        labels: MetricLabels = None,
    ) -> None:
        """Initialize the histogram.

        Args:
            name: Histogram name
            description: Histogram description
            buckets: Bucket boundaries
            labels: Optional histogram labels
        """
        super().__init__(name, description, labels)
        self.buckets = sorted(buckets)
        self._values: dict[str, list[int]] = {}

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Observe a value.

        Args:
            value: Value to observe
            labels: Optional label values
        """
        key = self._get_key(labels)
        if key not in self._values:
            self._values[key] = [0] * (len(self.buckets) + 1)

        # Find the appropriate bucket
        bucket_index = 0
        for i, bound in enumerate(self.buckets):
            if value <= bound:
                bucket_index = i
                break
        else:
            bucket_index = len(self.buckets)

        self._values[key][bucket_index] += 1

    def get_buckets(self, labels: dict[str, str] | None = None) -> dict[float, int]:
        """Get the current bucket values.

        Args:
            labels: Optional label values

        Returns:
            Dictionary mapping bucket boundaries to observation counts
        """
        key = self._get_key(labels)
        if key not in self._values:
            return {bound: 0 for bound in self.buckets}

        return {
            bound: count
            for bound, count in zip(self.buckets, self._values[key][:-1], strict=False)
        }


__all__ = [
    "MetricBase",
    "MetricCounter",
    "MetricGauge",
    "MetricHistogram",
    "MetricLabels",
    "MetricType",
    "MetricValue",
]
