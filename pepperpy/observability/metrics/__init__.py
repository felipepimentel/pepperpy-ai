"""Metrics collection for PepperPy.

This module provides functionality for collecting, aggregating, and reporting
metrics from PepperPy components and operations.
"""

from pepperpy.core.metrics import (
    Counter,
    Gauge,
    Histogram,
    Metric,
    MetricRecord,
    MetricsCollector,
    MetricsRegistry,
    MetricType,
    Summary,
)

# Re-export for backward compatibility
__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "Metric",
    "MetricRecord",
    "MetricsCollector",
    "MetricsRegistry",
    "MetricType",
    "Summary",
]
