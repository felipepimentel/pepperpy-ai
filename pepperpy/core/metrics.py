"""Metrics management system for PepperPy.

This module provides a unified metrics collection and reporting system
for tracking performance, usage, and other metrics across the framework.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricRecord:
    """Container for metric information."""

    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None


class Metric(ABC):
    """Base class for all metrics."""

    def __init__(
        self, name: str, description: str, labels: Optional[Dict[str, str]] = None
    ):
        """Initialize metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels
        """
        self.name = name
        self.description = description
        self.labels = labels or {}
        self._logger = logging.getLogger(f"pepperpy.metrics.{name}")
        self.type: MetricType = MetricType.GAUGE  # Default type

    @abstractmethod
    async def record(self, value: Any, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value.

        Args:
            value: Metric value
            labels: Optional additional labels
        """
        pass

    def create_record(
        self, value: float, labels: Optional[Dict[str, str]] = None
    ) -> MetricRecord:
        """Create a metric record.

        Args:
            value: Metric value
            labels: Optional additional labels

        Returns:
            Metric record
        """
        combined_labels = self.labels.copy()
        if labels:
            combined_labels.update(labels)

        return MetricRecord(
            name=self.name,
            type=self.type,
            value=value,
            labels=combined_labels,
            description=self.description,
        )


class Counter(Metric):
    """Counter metric that can only increase."""

    def __init__(
        self, name: str, description: str, labels: Optional[Dict[str, str]] = None
    ):
        """Initialize counter.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional counter labels
        """
        super().__init__(name, description, labels)
        self._value = 0.0
        self.type = MetricType.COUNTER

    async def record(
        self, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment counter.

        Args:
            value: Value to increment by (must be non-negative)
            labels: Optional additional labels

        Raises:
            ValueError: If value is negative
        """
        if value < 0:
            raise ValueError("Counter value cannot be negative")

        self._value += value
        self._logger.debug(f"Counter {self.name} incremented by {value}")


class Gauge(Metric):
    """Gauge metric that can go up and down."""

    def __init__(
        self, name: str, description: str, labels: Optional[Dict[str, str]] = None
    ):
        """Initialize gauge.

        Args:
            name: Gauge name
            description: Gauge description
            labels: Optional gauge labels
        """
        super().__init__(name, description, labels)
        self._value = 0.0
        self.type = MetricType.GAUGE

    async def record(
        self, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set gauge value.

        Args:
            value: New gauge value
            labels: Optional additional labels
        """
        self._value = value
        self._logger.debug(f"Gauge {self.name} set to {value}")


class Histogram(Metric):
    """Histogram metric for measuring distributions."""

    def __init__(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Initialize histogram.

        Args:
            name: Histogram name
            description: Histogram description
            buckets: Optional bucket boundaries
            labels: Optional histogram labels
        """
        super().__init__(name, description, labels)
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
        self._values: List[float] = []
        self.type = MetricType.HISTOGRAM

    async def record(
        self, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a value in the histogram.

        Args:
            value: Value to record
            labels: Optional additional labels
        """
        self._values.append(value)
        self._logger.debug(f"Histogram {self.name} recorded value {value}")


class Summary(Metric):
    """Summary metric for measuring distributions with quantiles."""

    def __init__(
        self,
        name: str,
        description: str,
        quantiles: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Initialize summary.

        Args:
            name: Summary name
            description: Summary description
            quantiles: Optional quantiles to track
            labels: Optional summary labels
        """
        super().__init__(name, description, labels)
        self.quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        self._values: List[float] = []
        self.type = MetricType.SUMMARY

    async def record(
        self, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a value in the summary.

        Args:
            value: Value to record
            labels: Optional additional labels
        """
        self._values.append(value)
        self._logger.debug(f"Summary {self.name} recorded value {value}")


class MetricsCollector:
    """Collector for system and application metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self._metrics: Dict[str, List[MetricRecord]] = {}
        self._registered_metrics: Dict[str, Metric] = {}

    def register_metric(self, metric: Metric) -> None:
        """Register a metric with the collector.

        Args:
            metric: Metric to register
        """
        self._registered_metrics[metric.name] = metric

    def record_metric(self, metric_record: MetricRecord) -> None:
        """Record a new metric.

        Args:
            metric_record: Metric record to store
        """
        if metric_record.name not in self._metrics:
            self._metrics[metric_record.name] = []
        self._metrics[metric_record.name].append(metric_record)

    async def record(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a value for a registered metric.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional metric labels

        Raises:
            ValueError: If metric is not registered
        """
        if name not in self._registered_metrics:
            raise ValueError(f"Metric '{name}' is not registered")

        metric = self._registered_metrics[name]
        await metric.record(value, labels)
        self.record_metric(metric.create_record(value, labels))

    def get_metric(self, name: str) -> List[MetricRecord]:
        """Get all recorded values for a specific metric.

        Args:
            name: Metric name

        Returns:
            List of metric records
        """
        return self._metrics.get(name, [])

    def get_latest_metric(self, name: str) -> Optional[MetricRecord]:
        """Get the most recent value for a specific metric.

        Args:
            name: Metric name

        Returns:
            Most recent metric record, or None if not found
        """
        metrics = self._metrics.get(name, [])
        if not metrics:
            return None
        return max(metrics, key=lambda m: m.timestamp)

    def get_all_metrics(self) -> Dict[str, List[MetricRecord]]:
        """Get all recorded metrics.

        Returns:
            Dictionary of metric names to lists of metric records
        """
        return self._metrics.copy()

    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()


class MetricsRegistry:
    """Registry for metrics collectors."""

    def __init__(self):
        """Initialize metrics registry."""
        self._collectors: Dict[str, MetricsCollector] = {}
        self._default_collector = MetricsCollector()

    def register_collector(self, name: str, collector: MetricsCollector) -> None:
        """Register a collector with the registry.

        Args:
            name: Collector name
            collector: Metrics collector
        """
        self._collectors[name] = collector

    def get_collector(self, name: str) -> Optional[MetricsCollector]:
        """Get a collector by name.

        Args:
            name: Collector name

        Returns:
            Metrics collector, or None if not found
        """
        return self._collectors.get(name)

    def record_metric(
        self, metric_record: MetricRecord, collector_name: Optional[str] = None
    ) -> None:
        """Record a metric using the specified collector.

        Args:
            metric_record: Metric record to store
            collector_name: Optional name of the collector to use
        """
        if collector_name:
            collector = self.get_collector(collector_name)
            if collector:
                collector.record_metric(metric_record)
            else:
                self._default_collector.record_metric(metric_record)
        else:
            self._default_collector.record_metric(metric_record)

    def get_all_metrics(self) -> Dict[str, Dict[str, List[MetricRecord]]]:
        """Get all metrics from all collectors.

        Returns:
            Dictionary of collector names to dictionaries of metric names to lists of metric records
        """
        result: Dict[str, Dict[str, List[MetricRecord]]] = {
            "default": self._default_collector.get_all_metrics()
        }
        for name, collector in self._collectors.items():
            result[name] = collector.get_all_metrics()
        return result
