"""Metrics management system.

This module provides functionality for collecting, tracking, and reporting metrics:

- MetricsManager: Core class for managing metrics collection
- Metric types: Counters, gauges, histograms, etc.
- Reporting: Exporting metrics to various backends
- Aggregation: Combining metrics across components
"""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

from .utils.dates import DateUtils


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()
    TIMER = auto()


@dataclass
class Metric:
    """Base class for metrics."""

    name: str
    description: str
    type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type.name,
            "tags": self.tags,
            "timestamp": self.timestamp,
        }


@dataclass
class CounterMetric(Metric):
    """Counter metric."""

    value: int = 0

    def __post_init__(self) -> None:
        """Initialize counter metric."""
        self.type = MetricType.COUNTER

    def increment(self, amount: int = 1) -> None:
        """Increment counter.

        Args:
            amount: Amount to increment
        """
        self.value += amount
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary.

        Returns:
            Dictionary representation
        """
        result = super().to_dict()
        result["value"] = self.value
        return result


@dataclass
class GaugeMetric(Metric):
    """Gauge metric."""

    value: float = 0.0

    def __post_init__(self) -> None:
        """Initialize gauge metric."""
        self.type = MetricType.GAUGE

    def set(self, value: float) -> None:
        """Set gauge value.

        Args:
            value: New value
        """
        self.value = value
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary.

        Returns:
            Dictionary representation
        """
        result = super().to_dict()
        result["value"] = self.value
        return result


@dataclass
class HistogramMetric(Metric):
    """Histogram metric."""

    values: List[float] = field(default_factory=list)
    buckets: List[float] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize histogram metric."""
        self.type = MetricType.HISTOGRAM
        if not self.buckets:
            self.buckets = [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, float("inf")]
        for bucket in self.buckets:
            self.counts[str(bucket)] = 0

    def observe(self, value: float) -> None:
        """Observe a value.

        Args:
            value: Value to observe
        """
        self.values.append(value)
        self.timestamp = time.time()
        for bucket in self.buckets:
            if value <= bucket:
                self.counts[str(bucket)] += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary.

        Returns:
            Dictionary representation
        """
        result = super().to_dict()
        result["values"] = self.values
        result["buckets"] = self.buckets
        result["counts"] = self.counts
        return result


@dataclass
class TimerMetric(Metric):
    """Timer metric."""

    start_time: Optional[float] = None
    duration: Optional[float] = None
    active: bool = False

    def __post_init__(self) -> None:
        """Initialize timer metric."""
        self.type = MetricType.TIMER

    def start(self) -> None:
        """Start timer."""
        self.start_time = time.time()
        self.active = True

    def stop(self) -> float:
        """Stop timer.

        Returns:
            Duration in seconds
        """
        if self.start_time is None:
            raise ValueError("Timer not started")
        self.duration = time.time() - self.start_time
        self.active = False
        self.timestamp = time.time()
        return self.duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary.

        Returns:
            Dictionary representation
        """
        result = super().to_dict()
        result["start_time"] = self.start_time
        result["duration"] = self.duration
        result["active"] = self.active
        return result


class MetricsManager:
    """Manager for metrics collection and reporting."""

    def __init__(self) -> None:
        """Initialize metrics manager."""
        self._metrics: Dict[str, Metric] = {}
        self._reporters: List[Callable[[Dict[str, Metric]], None]] = []
        self._tags: Dict[str, str] = {}

    def register_metric(self, metric: Metric) -> None:
        """Register a metric.

        Args:
            metric: Metric to register
        """
        # Add global tags
        for key, value in self._tags.items():
            if key not in metric.tags:
                metric.tags[key] = value
        self._metrics[metric.name] = metric

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name.

        Args:
            name: Metric name

        Returns:
            Metric if found, None otherwise
        """
        return self._metrics.get(name)

    def add_reporter(self, reporter: Callable[[Dict[str, Metric]], None]) -> None:
        """Add a metrics reporter.

        Args:
            reporter: Reporter function
        """
        self._reporters.append(reporter)

    def set_tag(self, key: str, value: str) -> None:
        """Set a global tag.

        Args:
            key: Tag key
            value: Tag value
        """
        self._tags[key] = value
        # Update existing metrics
        for metric in self._metrics.values():
            if key not in metric.tags:
                metric.tags[key] = value

    def create_counter(
        self, name: str, description: str, tags: Optional[Dict[str, str]] = None
    ) -> CounterMetric:
        """Create a counter metric.

        Args:
            name: Metric name
            description: Metric description
            tags: Optional tags

        Returns:
            Counter metric
        """
        metric = CounterMetric(
            name=name, description=description, tags=tags or {}, type=MetricType.COUNTER
        )
        self.register_metric(metric)
        return metric

    def create_gauge(
        self, name: str, description: str, tags: Optional[Dict[str, str]] = None
    ) -> GaugeMetric:
        """Create a gauge metric.

        Args:
            name: Metric name
            description: Metric description
            tags: Optional tags

        Returns:
            Gauge metric
        """
        metric = GaugeMetric(
            name=name, description=description, tags=tags or {}, type=MetricType.GAUGE
        )
        self.register_metric(metric)
        return metric

    def create_histogram(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> HistogramMetric:
        """Create a histogram metric.

        Args:
            name: Metric name
            description: Metric description
            buckets: Optional bucket boundaries
            tags: Optional tags

        Returns:
            Histogram metric
        """
        metric = HistogramMetric(
            name=name,
            description=description,
            buckets=buckets or [],
            tags=tags or {},
            type=MetricType.HISTOGRAM,
        )
        self.register_metric(metric)
        return metric

    def create_timer(
        self, name: str, description: str, tags: Optional[Dict[str, str]] = None
    ) -> TimerMetric:
        """Create a timer metric.

        Args:
            name: Metric name
            description: Metric description
            tags: Optional tags

        Returns:
            Timer metric
        """
        metric = TimerMetric(
            name=name, description=description, tags=tags or {}, type=MetricType.TIMER
        )
        self.register_metric(metric)
        return metric

    def report(self) -> None:
        """Report metrics to all reporters."""
        for reporter in self._reporters:
            reporter(self._metrics)

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics = {}

    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics.

        Returns:
            Dictionary of metrics
        """
        return self._metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics manager to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "metrics": {
                name: metric.to_dict() for name, metric in self._metrics.items()
            },
            "tags": self._tags,
            "timestamp": DateUtils.utc_now().isoformat(),
        }
