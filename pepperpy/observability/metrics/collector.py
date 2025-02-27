"""Metrics collection functionality for PepperPy observability.

This module provides functionality for collecting, aggregating, and managing
various metrics from PepperPy components and operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Container for metric information."""

    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None


class MetricsCollector:
    """Collector for system and application metrics."""

    def __init__(self):
        self._metrics: Dict[str, List[Metric]] = {}

    def record_metric(self, metric: Metric) -> None:
        """Record a new metric."""
        if metric.name not in self._metrics:
            self._metrics[metric.name] = []
        self._metrics[metric.name].append(metric)

    def get_metric(self, name: str) -> List[Metric]:
        """Get all recorded values for a specific metric."""
        return self._metrics.get(name, [])

    def get_latest_metric(self, name: str) -> Optional[Metric]:
        """Get the most recent value for a specific metric."""
        metrics = self._metrics.get(name, [])
        return metrics[-1] if metrics else None

    def get_all_metrics(self) -> Dict[str, List[Metric]]:
        """Get all recorded metrics."""
        return self._metrics.copy()

    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()


class MetricsRegistry:
    """Registry for managing multiple metric collectors."""

    def __init__(self):
        self._collectors: Dict[str, MetricsCollector] = {}
        self._default_collector = MetricsCollector()

    def register_collector(self, name: str, collector: MetricsCollector) -> None:
        """Register a new metrics collector."""
        self._collectors[name] = collector

    def get_collector(self, name: str) -> Optional[MetricsCollector]:
        """Get a specific metrics collector."""
        return self._collectors.get(name)

    def record_metric(
        self, metric: Metric, collector_name: Optional[str] = None
    ) -> None:
        """Record a metric using the specified collector or the default one."""
        if collector_name:
            collector = self._collectors.get(collector_name)
            if collector is None:
                collector = self._default_collector
        else:
            collector = self._default_collector
        collector.record_metric(metric)

    def get_all_metrics(self) -> Dict[str, Dict[str, List[Metric]]]:
        """Get all metrics from all collectors."""
        all_metrics = {"default": self._default_collector.get_all_metrics()}
        for name, collector in self._collectors.items():
            all_metrics[name] = collector.get_all_metrics()
        return all_metrics
