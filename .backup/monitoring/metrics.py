"""Metrics module for Pepperpy.

This module provides functionality for collecting and reporting metrics.
"""

from enum import Enum
from typing import Any, Dict, Optional


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricCollector:
    """Collects and manages metrics."""

    def __init__(self):
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def record(
        self, name: str, value: Any, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric value."""
        if name not in self._metrics:
            self._metrics[name] = {"values": [], "tags": tags or {}}
        self._metrics[name]["values"].append(value)

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all recorded metrics."""
        return self._metrics

    def clear(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()


# Global collector instance
collector = MetricCollector()


async def record_metric(
    name: str,
    value: float,
    metric_type: MetricType,
    labels: Optional[Dict[str, str]] = None,
    description: Optional[str] = None,
) -> None:
    """Record a metric value using the global collector.

    Args:
        name: Metric name
        value: Metric value
        metric_type: Type of metric
        labels: Optional metric labels
        description: Optional metric description

    """
    collector.record(name, value, labels)
