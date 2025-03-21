"""Monitoring and metrics collection for PepperPy.
 
This module provides functionality for collecting and managing metrics
across the PepperPy framework, including performance metrics, usage
statistics, and system health information.

Note: This module is deprecated and will be removed in a future version.
Please use the metrics module instead.
"""

# Re-export classes and functions from metrics.py
from .metrics import (
    Metric,
    MetricCategory,
    MetricsCollector,
    PerformanceTracker,
    benchmark,
    get_memory_usage,
    get_system_info,
    measure_memory,
    measure_time,
    performance_tracker,
    report_custom_metric,
)

__all__ = [
    "Metric",
    "MetricCategory",
    "MetricsCollector",
    "PerformanceTracker",
    "benchmark",
    "get_memory_usage",
    "get_system_info",
    "measure_memory",
    "measure_time",
    "performance_tracker",
    "report_custom_metric",
]
