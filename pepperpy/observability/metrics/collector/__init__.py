"""Specialized metric collectors for different subsystems.

This module provides specialized metric collectors for different parts of the system:
- System metrics collectors for hardware and OS-level metrics
- Application metrics collectors for application-specific metrics
- Performance metrics collectors for tracking performance data
- Custom collectors for domain-specific metrics

These collectors extend the base MetricsCollector functionality with specialized
collection, aggregation, and reporting capabilities for different metric types
and sources.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()


class Metric(ABC):
    """Base class for all metrics."""

    def __init__(self, name: str, description: str, metric_type: MetricType):
        """Initialize a metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
            metric_type: The type of metric
        """
        self.name = name
        self.description = description
        self.metric_type = metric_type

    @abstractmethod
    def record(self, value: Any) -> None:
        """Record a value for this metric.

        Args:
            value: The value to record
        """
        pass


class MetricsCollector:
    """Base class for all metrics collectors."""

    def __init__(self, name: str):
        """Initialize a metrics collector.

        Args:
            name: The name of the collector
        """
        self.name = name
        self.metrics: Dict[str, Metric] = {}

    def register_metric(self, metric: Metric) -> None:
        """Register a metric with this collector.

        Args:
            metric: The metric to register
        """
        self.metrics[metric.name] = metric

    def record(self, metric_name: str, value: Any) -> None:
        """Record a value for a metric.

        Args:
            metric_name: The name of the metric
            value: The value to record
        """
        if metric_name in self.metrics:
            self.metrics[metric_name].record(value)


# Import specialized collectors here as they are implemented
# from .system import SystemMetricsCollector
# from .application import ApplicationMetricsCollector
# from .performance import PerformanceMetricsCollector

# Export public API
__all__ = [
    "Metric",
    "MetricType",
    "MetricsCollector",
    # Add specialized collectors here as they are implemented
    # "SystemMetricsCollector",
    # "ApplicationMetricsCollector",
    # "PerformanceMetricsCollector",
]
