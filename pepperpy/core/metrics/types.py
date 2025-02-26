"""Core metric types for Pepperpy."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from pepperpy.core.protocols.lifecycle import Lifecycle

MetricValue = Union[int, float]
MetricLabels = Union[Dict[str, str], None]


class MetricBase(Lifecycle):
    """Base class for all metrics."""

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: MetricLabels = None,
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

    def _get_key(self, labels: Optional[Dict[str, str]] = None) -> str:
        """Get metric key with labels.

        Args:
            labels: Optional label values

        Returns:
            Metric key with labels
        """
        if not labels:
            return self.name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{self.name}{{{label_str}}}"

    async def initialize(self) -> None:
        """Initialize metric."""
        pass

    async def cleanup(self) -> None:
        """Clean up metric."""
        pass


class Counter(MetricBase):
    """Counter metric type.

    Counters can only increase in value and reset when the process restarts.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: MetricLabels = None,
    ) -> None:
        """Initialize counter.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional counter labels
        """
        super().__init__(name, description, labels)
        self._values: Dict[str, float] = {}

    async def inc(self, value: float = 1.0, labels: MetricLabels = None) -> None:
        """Increment counter.

        Args:
            value: Value to increment by
            labels: Optional label values
        """
        key = self._get_key(labels)
        self._values[key] = self._values.get(key, 0.0) + value

    async def get(self, labels: MetricLabels = None) -> float:
        """Get current counter value.

        Args:
            labels: Optional label values

        Returns:
            Current counter value
        """
        return self._values.get(self._get_key(labels), 0.0)


class Gauge(MetricBase):
    """Gauge metric type.

    Gauges can increase and decrease in value.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: MetricLabels = None,
    ) -> None:
        """Initialize gauge.

        Args:
            name: Gauge name
            description: Gauge description
            labels: Optional gauge labels
        """
        super().__init__(name, description, labels)
        self._values: Dict[str, float] = {}

    async def set(self, value: float, labels: MetricLabels = None) -> None:
        """Set gauge value.

        Args:
            value: Value to set
            labels: Optional label values
        """
        self._values[self._get_key(labels)] = value

    async def inc(self, value: float = 1.0, labels: MetricLabels = None) -> None:
        """Increment gauge.

        Args:
            value: Value to increment by
            labels: Optional label values
        """
        key = self._get_key(labels)
        self._values[key] = self._values.get(key, 0.0) + value

    async def dec(self, value: float = 1.0, labels: MetricLabels = None) -> None:
        """Decrement gauge.

        Args:
            value: Value to decrement by
            labels: Optional label values
        """
        self.inc(-value, labels)

    async def get(self, labels: MetricLabels = None) -> float:
        """Get current gauge value.

        Args:
            labels: Optional label values

        Returns:
            Current gauge value
        """
        return self._values.get(self._get_key(labels), 0.0)


class Histogram(MetricBase):
    """Histogram metric type.

    Histograms track the size and number of events in buckets.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: list[float] | None = None,
        labels: MetricLabels = None,
    ) -> None:
        """Initialize histogram.

        Args:
            name: Histogram name
            description: Histogram description
            buckets: Optional bucket boundaries
            labels: Optional histogram labels
        """
        super().__init__(name, description, labels)
        self.buckets = sorted(buckets) if buckets else [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        self._values: Dict[str, list[int]] = {}

    async def observe(self, value: float, labels: MetricLabels = None) -> None:
        """Observe a value.

        Args:
            value: Value to observe
            labels: Optional label values
        """
        key = self._get_key(labels)
        if key not in self._values:
            self._values[key] = [0] * (len(self.buckets) + 1)

        # Find appropriate bucket
        bucket_index = 0
        for i, bound in enumerate(self.buckets):
            if value <= bound:
                bucket_index = i
                break
        else:
            bucket_index = len(self.buckets)

        self._values[key][bucket_index] += 1

    async def get_buckets(self, labels: MetricLabels = None) -> Dict[float, int]:
        """Get current bucket values.

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
            for bound, count in zip(self.buckets, self._values[key][:-1])
        }


__all__ = [
    "MetricBase",
    "Counter",
    "Gauge",
    "Histogram",
    "MetricValue",
    "MetricLabels",
] 