"""Base metrics implementation for the Pepperpy framework.

This module provides the core metric implementations used throughout the framework.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pepperpy.core.metrics.types import Metric

logger = logging.getLogger(__name__)


@dataclass
class MetricConfig:
    """Configuration for metrics."""

    name: str
    description: str
    labels: dict[str, str] = field(default_factory=dict)
    buckets: list[float] | None = None


class Counter(Metric):
    """Counter metric.

    This class implements a counter metric that can only increase.
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize counter.

        Args:
            name: Counter name
            description: Counter description
        """
        self._name = name
        self._description = description
        self._value = 0.0

    def inc(self, value: float = 1.0) -> None:
        """Increment counter.

        Args:
            value: Value to increment by
        """
        if value < 0:
            raise ValueError("Counter can only be incremented by non-negative values")
        self._value += value

    def observe(self, value: float) -> None:
        """Not implemented for counters."""
        raise NotImplementedError("Counter does not support observe()")

    def get_value(self) -> float:
        """Get counter value.

        Returns:
            Current counter value
        """
        return self._value


class Histogram(Metric):
    """Histogram metric.

    This class implements a histogram metric that tracks value distributions.
    """

    def __init__(
        self,
        name: str,
        description: str,
        buckets: list[float] | None = None,
    ) -> None:
        """Initialize histogram.

        Args:
            name: Histogram name
            description: Histogram description
            buckets: Optional bucket boundaries
        """
        self._name = name
        self._description = description
        self._buckets = sorted(buckets or [0.1, 0.5, 1.0, 2.0, 5.0])
        self._values: list[float] = []

    def inc(self, value: float = 1.0) -> None:
        """Not implemented for histograms."""
        raise NotImplementedError("Histogram does not support inc()")

    def observe(self, value: float) -> None:
        """Record observation.

        Args:
            value: Value to record
        """
        self._values.append(value)

    def get_value(self) -> dict[str, Any]:
        """Get histogram value.

        Returns:
            Dict containing count, sum, and buckets
        """
        if not self._values:
            return {
                "count": 0,
                "sum": 0.0,
                "buckets": {str(b): 0 for b in self._buckets},
            }

        count = len(self._values)
        total = sum(self._values)
        buckets = {
            str(b): sum(1 for v in self._values if v <= b) for b in self._buckets
        }

        return {
            "count": count,
            "sum": total,
            "buckets": buckets,
        }


class Gauge(Metric):
    """Gauge metric.

    This class implements a gauge metric that can go up and down.
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize gauge.

        Args:
            name: Gauge name
            description: Gauge description
        """
        self._name = name
        self._description = description
        self._value = 0.0

    def inc(self, value: float = 1.0) -> None:
        """Increment gauge.

        Args:
            value: Value to increment by
        """
        self._value += value

    def dec(self, value: float = 1.0) -> None:
        """Decrement gauge.

        Args:
            value: Value to decrement by
        """
        self._value -= value

    def set(self, value: float) -> None:
        """Set gauge value.

        Args:
            value: Value to set
        """
        self._value = value

    def observe(self, value: float) -> None:
        """Set gauge value.

        Args:
            value: Value to set
        """
        self.set(value)

    def get_value(self) -> float:
        """Get gauge value.

        Returns:
            Current gauge value
        """
        return self._value


class Summary(Metric):
    """Summary metric.

    This class implements a summary metric that tracks value distributions
    with quantiles.
    """

    def __init__(
        self,
        name: str,
        description: str,
        quantiles: list[float] | None = None,
    ) -> None:
        """Initialize summary.

        Args:
            name: Summary name
            description: Summary description
            quantiles: Optional quantile values
        """
        self._name = name
        self._description = description
        self._quantiles = sorted(quantiles or [0.5, 0.9, 0.99])
        self._values: list[float] = []

    def inc(self, value: float = 1.0) -> None:
        """Not implemented for summaries."""
        raise NotImplementedError("Summary does not support inc()")

    def observe(self, value: float) -> None:
        """Record observation.

        Args:
            value: Value to record
        """
        self._values.append(value)

    def get_value(self) -> dict[str, Any]:
        """Get summary value.

        Returns:
            Dict containing count, sum, and quantiles
        """
        if not self._values:
            return {
                "count": 0,
                "sum": 0.0,
                "quantiles": {str(q): 0.0 for q in self._quantiles},
            }

        count = len(self._values)
        total = sum(self._values)
        sorted_values = sorted(self._values)

        quantiles = {}
        for q in self._quantiles:
            idx = int(q * count)
            if idx >= count:
                idx = count - 1
            quantiles[str(q)] = sorted_values[idx]

        return {
            "count": count,
            "sum": total,
            "quantiles": quantiles,
        }


class MetricsManager:
    """Manager for metrics.

    This class provides a central registry for metrics and handles metric
    collection and export.
    """

    def __init__(self) -> None:
        """Initialize manager."""
        self._metrics: dict[str, dict[str, Metric]] = {}
        self._logger = logging.getLogger(__name__)

    def register_metric(
        self,
        metric: Metric,
        metric_type: str,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Register a metric.

        Args:
            metric: Metric to register
            metric_type: Type of metric
            labels: Optional metric labels
        """
        name = getattr(metric, "_name", str(id(metric)))
        labels_str = ",".join(f"{k}={v}" for k, v in (labels or {}).items())
        key = f"{name}:{labels_str}"

        if metric_type not in self._metrics:
            self._metrics[metric_type] = {}

        self._metrics[metric_type][key] = metric

    async def create_counter(
        self,
        name: str,
        description: str,
        labels: dict[str, str] | None = None,
    ) -> Counter:
        """Create and register a counter.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional counter labels

        Returns:
            Created counter
        """
        counter = Counter(name, description)
        self.register_metric(counter, "counter", labels)
        return counter

    async def create_histogram(
        self,
        name: str,
        description: str,
        buckets: list[float] | None = None,
        labels: dict[str, str] | None = None,
    ) -> Histogram:
        """Create and register a histogram.

        Args:
            name: Histogram name
            description: Histogram description
            buckets: Optional bucket boundaries
            labels: Optional histogram labels

        Returns:
            Created histogram
        """
        histogram = Histogram(name, description, buckets)
        self.register_metric(histogram, "histogram", labels)
        return histogram

    async def create_gauge(
        self,
        name: str,
        description: str,
        labels: dict[str, str] | None = None,
    ) -> Gauge:
        """Create and register a gauge.

        Args:
            name: Gauge name
            description: Gauge description
            labels: Optional gauge labels

        Returns:
            Created gauge
        """
        gauge = Gauge(name, description)
        self.register_metric(gauge, "gauge", labels)
        return gauge

    async def create_summary(
        self,
        name: str,
        description: str,
        quantiles: list[float] | None = None,
        labels: dict[str, str] | None = None,
    ) -> Summary:
        """Create and register a summary.

        Args:
            name: Summary name
            description: Summary description
            quantiles: Optional quantile values
            labels: Optional summary labels

        Returns:
            Created summary
        """
        summary = Summary(name, description, quantiles)
        self.register_metric(summary, "summary", labels)
        return summary

    def get_metrics(self) -> dict[str, dict[str, Any]]:
        """Get all metrics.

        Returns:
            Dict of metric types to metric values
        """
        result = {}
        for metric_type, metrics in self._metrics.items():
            result[metric_type] = {
                key: metric.get_value() for key, metric in metrics.items()
            }
        return result
