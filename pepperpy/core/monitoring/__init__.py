"""Core monitoring module.

This module provides a unified monitoring system with support for:
- Structured logging with context
- Metrics collection and export
- Distributed tracing
- Performance monitoring
"""

from .logging import LoggingError, get_logger, logger_manager, setup_logging
from .metrics import Metric, MetricsError, MetricsManager, metrics_manager
from .tracing import Span, SpanContext, TracingError, TracingManager
from .types import LogLevel, MetricType, MonitoringError

__all__ = [
    # Core types
    "LogLevel",
    "MetricType",
    "MonitoringError",
    # Logging
    "LoggingError",
    "get_logger",
    "logger_manager",
    "setup_logging",
    # Metrics
    "Metric",
    "MetricsError",
    "MetricsManager",
    "metrics_manager",
    # Tracing
    "Span",
    "SpanContext",
    "TracingError",
    "TracingManager",
]
