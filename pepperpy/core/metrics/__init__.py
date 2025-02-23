"""Metrics system for the Pepperpy framework.

This module provides metrics functionality:
- Metric types (Counter, Gauge, Histogram, Summary)
- Metric registration and management
- Metric collection and export
"""

from pepperpy.core.metrics.base import (
    Counter,
    Gauge,
    Histogram,
    Metric,
    MetricConfig,
    MetricsManager,
    Summary,
)
from pepperpy.core.metrics.types import (
    MetricCounter,
    MetricHistogram,
    T_Metric,
)

# Initialize core metrics manager
metrics_manager = MetricsManager()

__all__ = [
    # Base classes
    "Counter",
    "Gauge",
    "Histogram",
    "Summary",
    "Metric",
    "MetricConfig",
    "MetricsManager",
    # Type definitions
    "MetricCounter",
    "MetricHistogram",
    "T_Metric",
    # Instances
    "metrics_manager",
]
