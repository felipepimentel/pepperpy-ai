"""Monitoring system for the Pepperpy framework.

This module provides monitoring functionality:
- Metrics collection and export
- Logging configuration
- Telemetry integration
"""

from typing import Optional

from pepperpy.core.metrics import metrics_manager
from pepperpy.core.metrics.base import (
    Counter,
    Gauge,
    Histogram,
    MetricsManager,
    Summary,
)
from pepperpy.monitoring.logging import configure_logging, logger
from pepperpy.monitoring.metrics.collectors import (
    LoggingCollector,
    OpenTelemetryCollector,
    PrometheusCollector,
)
from pepperpy.monitoring.metrics.exporters import (
    ConsoleExporter,
    FileExporter,
    HTTPExporter,
)

__all__ = [
    # Logging
    "configure_logging",
    "logger",
    # Metrics
    "Counter",
    "Gauge",
    "Histogram",
    "Summary",
    "MetricsManager",
    "metrics_manager",
    # Collectors
    "LoggingCollector",
    "OpenTelemetryCollector",
    "PrometheusCollector",
    # Exporters
    "ConsoleExporter",
    "FileExporter",
    "HTTPExporter",
]
