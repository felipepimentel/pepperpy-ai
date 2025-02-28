"""Metrics management system.

This module provides functionality for collecting, tracking, and reporting metrics:

- MetricsManager: Core class for managing metrics collection
- Metric types: Counters, gauges, histograms, etc.
- Reporting: Exporting metrics to various backends
- Aggregation: Combining metrics across components
"""

# Import directly from the core metrics module
from pepperpy.core.metrics import (
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
    Metric,
    MetricsManager,
    MetricType,
    TimerMetric,
)

__all__ = [
    "MetricsManager",
    "Metric",
    "MetricType",
    "CounterMetric",
    "GaugeMetric",
    "HistogramMetric",
    "TimerMetric",
]
