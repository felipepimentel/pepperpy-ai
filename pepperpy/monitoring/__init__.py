"""Monitoring module for Pepperpy.

This module provides logging and monitoring utilities for the framework.
"""

import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

# Configure root logger
logger = logging.getLogger("pepperpy")
logger.setLevel(logging.INFO)

# Add console handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class Metric:
    """Base class for metrics."""

    name: str
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Counter(Metric):
    """Counter metric type."""

    value: int = 0

    def increment(self, amount: int = 1) -> None:
        """Increment the counter."""
        self.value += amount
        self.timestamp = datetime.now()


@dataclass
class Gauge(Metric):
    """Gauge metric type."""

    value: float = 0.0

    def set(self, value: float) -> None:
        """Set the gauge value."""
        self.value = value
        self.timestamp = datetime.now()

    def increment(self, amount: float = 1.0) -> None:
        """Increment the gauge."""
        self.value += amount
        self.timestamp = datetime.now()

    def decrement(self, amount: float = 1.0) -> None:
        """Decrement the gauge."""
        self.value -= amount
        self.timestamp = datetime.now()


@dataclass
class Histogram(Metric):
    """Histogram metric type."""

    values: List[float] = field(default_factory=list)
    count: int = 0
    sum: float = 0.0
    buckets: List[float] = field(
        default_factory=lambda: [
            0.005,
            0.01,
            0.025,
            0.05,
            0.075,
            0.1,
            0.25,
            0.5,
            0.75,
            1.0,
            2.5,
            5.0,
            7.5,
            10.0,
        ]
    )

    def observe(self, value: float) -> None:
        """Record a value observation."""
        self.values.append(value)
        self.count += 1
        self.sum += value
        self.timestamp = datetime.now()


class MetricsRegistry:
    """Registry for metrics."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._metrics: Dict[str, Metric] = {}

    def register(self, metric: Metric) -> None:
        """Register a metric.

        Args:
            metric: Metric to register
        """
        if metric is None:
            raise ValueError("Cannot register None as a metric")
        self._metrics[metric.name] = metric

    def get(self, name: str) -> Optional[Metric]:
        """Get a metric by name.

        Args:
            name: Name of the metric

        Returns:
            Metric if found, None otherwise
        """
        return self._metrics.get(name)

    def clear(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()

    async def record_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: Union[MetricType, str],
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a metric value.

        Args:
            name: Name of the metric
            value: Value to record
            metric_type: Type of metric
            description: Optional description
            labels: Optional labels
        """
        if not name:
            raise ValueError("Metric name cannot be empty")

        # Convert string to enum if needed
        if isinstance(metric_type, str):
            metric_type = MetricType(metric_type)

        metric = self.get(name)
        if metric is None:
            labels = labels or {}
            if metric_type == MetricType.COUNTER:
                metric = Counter(
                    name=name,
                    description=description,
                    labels=labels,
                    value=int(value),
                )
            elif metric_type == MetricType.GAUGE:
                metric = Gauge(
                    name=name,
                    description=description,
                    labels=labels,
                    value=float(value),
                )
            elif metric_type == MetricType.HISTOGRAM:
                metric = Histogram(
                    name=name,
                    description=description,
                    labels=labels,
                )
                metric.observe(float(value))
            else:
                raise ValueError(f"Invalid metric type: {metric_type}")
            self.register(metric)
        else:
            if isinstance(metric, Counter) and isinstance(value, (int, float)):
                metric.value = int(value)
            elif isinstance(metric, Gauge):
                metric.value = float(value)
            elif isinstance(metric, Histogram):
                metric.observe(float(value))


# Create global metrics registry
metrics = MetricsRegistry()

# Expose public interface
__all__ = [
    "logger",
    "metrics",
    "Counter",
    "Gauge",
    "Histogram",
    "MetricType",
]
