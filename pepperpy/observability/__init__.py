"""Unified observability system for PepperPy.

This module provides a unified interface for metrics, logging, tracing,
and health checks. It allows for consistent monitoring and debugging
across the entire application.

Example:
    >>> from pepperpy.observability import UnifiedObservabilityProvider
    >>> provider = UnifiedObservabilityProvider()
    >>> await provider.initialize()
    >>> await provider.record_metric("requests_total", 1, MetricType.COUNTER)
    >>> await provider.log("Request processed", LogLevel.INFO)
    >>> await provider.cleanup()
"""

from .base import ObservabilityProvider
from .errors import (
    ConfigurationError,
    CorrelationError,
    ExporterError,
    HealthCheckError,
    LoggingError,
    MetricsError,
    ObservabilityError,
    TracingError,
    ValidationError,
)
from .provider import UnifiedObservabilityProvider
from .types import (
    Context,
    HealthCheck,
    HealthStatus,
    LogLevel,
    LogRecord,
    Metric,
    MetricType,
    MetricValue,
    Span,
    Tags,
)

__all__ = [
    # Main classes
    "ObservabilityProvider",
    "UnifiedObservabilityProvider",
    # Data classes
    "Metric",
    "LogRecord",
    "Span",
    "HealthCheck",
    # Enums
    "MetricType",
    "LogLevel",
    "HealthStatus",
    # Type aliases
    "MetricValue",
    "Tags",
    "Context",
    # Exceptions
    "ObservabilityError",
    "MetricsError",
    "LoggingError",
    "TracingError",
    "HealthCheckError",
    "CorrelationError",
    "ExporterError",
    "ConfigurationError",
    "ValidationError",
]

__version__ = "1.0.0"
