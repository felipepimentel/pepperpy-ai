"""Core metrics module.

This module provides metrics and monitoring functionality.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, Union, cast

# Type aliases
MetricValue = Union[int, float, str]
MetricLabels = dict[str, str]

# Generic type for metrics
T = TypeVar("T", bound="MetricBase")


class MetricType(str, Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricBase:
    """Base class for metrics."""

    name: str
    description: str
    type: MetricType
    labels: MetricLabels

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


@dataclass
class MetricCounter(MetricBase):
    """Counter metric."""

    value: int

    def __post_init__(self):
        super().__post_init__()
        self.type = MetricType.COUNTER


@dataclass
class MetricGauge(MetricBase):
    """Gauge metric."""

    value: float

    def __post_init__(self):
        super().__post_init__()
        self.type = MetricType.GAUGE


@dataclass
class MetricHistogram(MetricBase):
    """Histogram metric."""

    buckets: list[float]
    values: list[float]

    def __post_init__(self):
        super().__post_init__()
        self.type = MetricType.HISTOGRAM
        if self.values is None:
            self.values = []


@dataclass
class MetricSummary(MetricBase):
    """Summary metric."""

    quantiles: list[float]
    values: list[float]

    def __post_init__(self):
        super().__post_init__()
        self.type = MetricType.SUMMARY
        if self.values is None:
            self.values = []


class MetricsManager:
    """Manages metrics collection and reporting."""

    def __init__(self):
        """Initialize metrics manager."""
        self._metrics: dict[str, MetricBase] = {}

    def counter(
        self,
        name: str,
        description: str,
        labels: MetricLabels | None = None,
    ) -> MetricCounter:
        """Create or get a counter metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels

        Returns:
            Counter metric
        """
        key = f"counter_{name}"
        if key not in self._metrics:
            self._metrics[key] = MetricCounter(
                name, description, MetricType.COUNTER, labels or {}, 0
            )
        return cast(MetricCounter, self._metrics[key])

    def gauge(
        self,
        name: str,
        description: str,
        labels: MetricLabels | None = None,
    ) -> MetricGauge:
        """Create or get a gauge metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels

        Returns:
            Gauge metric
        """
        key = f"gauge_{name}"
        if key not in self._metrics:
            self._metrics[key] = MetricGauge(
                name, description, MetricType.GAUGE, labels or {}, 0.0
            )
        return cast(MetricGauge, self._metrics[key])

    def histogram(
        self,
        name: str,
        description: str,
        buckets: list[float],
        labels: MetricLabels | None = None,
    ) -> MetricHistogram:
        """Create or get a histogram metric.

        Args:
            name: Metric name
            description: Metric description
            buckets: Histogram buckets
            labels: Optional metric labels

        Returns:
            Histogram metric
        """
        key = f"histogram_{name}"
        if key not in self._metrics:
            self._metrics[key] = MetricHistogram(
                name,
                description,
                MetricType.HISTOGRAM,
                labels or {},
                buckets,
                [],
            )
        return cast(MetricHistogram, self._metrics[key])

    def summary(
        self,
        name: str,
        description: str,
        quantiles: list[float],
        labels: MetricLabels | None = None,
    ) -> MetricSummary:
        """Create or get a summary metric.

        Args:
            name: Metric name
            description: Metric description
            quantiles: Summary quantiles
            labels: Optional metric labels

        Returns:
            Summary metric
        """
        key = f"summary_{name}"
        if key not in self._metrics:
            self._metrics[key] = MetricSummary(
                name,
                description,
                MetricType.SUMMARY,
                labels or {},
                quantiles,
                [],
            )
        return cast(MetricSummary, self._metrics[key])

    def get_metric(self, name: str) -> MetricBase:
        """Get a metric by name.

        Args:
            name: Metric name

        Returns:
            Metric instance

        Raises:
            KeyError: If metric not found
        """
        for key, metric in self._metrics.items():
            if key.endswith(name):
                return metric
        raise KeyError(f"Metric {name} not found")

    def get_counter(self, name: str) -> MetricCounter:
        """Get a counter metric by name.

        Args:
            name: Metric name

        Returns:
            Counter metric

        Raises:
            KeyError: If metric not found
            TypeError: If metric is not a counter
        """
        metric = self.get_metric(name)
        if not isinstance(metric, MetricCounter):
            raise TypeError(f"Metric {name} is not a counter")
        return metric

    def get_gauge(self, name: str) -> MetricGauge:
        """Get a gauge metric by name.

        Args:
            name: Metric name

        Returns:
            Gauge metric

        Raises:
            KeyError: If metric not found
            TypeError: If metric is not a gauge
        """
        metric = self.get_metric(name)
        if not isinstance(metric, MetricGauge):
            raise TypeError(f"Metric {name} is not a gauge")
        return metric

    def get_histogram(self, name: str) -> MetricHistogram:
        """Get a histogram metric by name.

        Args:
            name: Metric name

        Returns:
            Histogram metric

        Raises:
            KeyError: If metric not found
            TypeError: If metric is not a histogram
        """
        metric = self.get_metric(name)
        if not isinstance(metric, MetricHistogram):
            raise TypeError(f"Metric {name} is not a histogram")
        return metric

    def get_summary(self, name: str) -> MetricSummary:
        """Get a summary metric by name.

        Args:
            name: Metric name

        Returns:
            Summary metric

        Raises:
            KeyError: If metric not found
            TypeError: If metric is not a summary
        """
        metric = self.get_metric(name)
        if not isinstance(metric, MetricSummary):
            raise TypeError(f"Metric {name} is not a summary")
        return metric

    def get_all_metrics(self) -> dict[str, MetricBase]:
        """Get all metrics.

        Returns:
            Dictionary mapping metric names to metrics
        """
        return self._metrics.copy()


# Global metrics manager instance
metrics_manager = MetricsManager()


# Export public API
__all__ = [
    "MetricBase",
    "MetricCounter",
    "MetricGauge",
    "MetricHistogram",
    "MetricLabels",
    "MetricSummary",
    "MetricType",
    "MetricValue",
    "MetricsManager",
    "metrics_manager",
]
