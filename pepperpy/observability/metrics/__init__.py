"""Metrics collection for PepperPy.

This module provides metrics collection capabilities for the PepperPy framework:
- Counters: Track cumulative values
- Gauges: Track values that can increase and decrease
- Histograms: Track distributions of values
- Exporters: Export metrics to various backends
- Model Performance: Track and analyze AI model performance metrics

The metrics system enables applications to collect and analyze quantitative data
about their operation, facilitating performance analysis and optimization.
"""

from .collector import Metric, MetricsCollector, MetricType
from .manager import MetricsRegistry
from .model_performance import (
    ModelCallEvent,
    ModelMetrics,
    PerformanceAnalyzer,
    PerformanceMonitor,
    PerformanceReporter,
    PerformanceTracker,
)

# Export public API
__all__ = [
    # Metrics core
    "Metric",
    "MetricsCollector",
    "MetricType",
    "MetricsRegistry",
    # Model performance
    "ModelCallEvent",
    "ModelMetrics",
    "PerformanceTracker",
    "PerformanceAnalyzer",
    "PerformanceMonitor",
    "PerformanceReporter",
]
