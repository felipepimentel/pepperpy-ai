"""Observability framework for PepperPy.

This module provides comprehensive observability capabilities for the PepperPy framework:
- Logging: Structured logging with context and correlation
- Metrics: Performance and operational metrics collection
- Tracing: Distributed tracing for request flows
- Health: System health checks and status reporting
- Monitoring: System monitoring and alerting
- Audit: Security and compliance audit logging

The observability framework enables visibility into the behavior, performance, and
health of applications built with PepperPy, facilitating debugging, optimization,
and operational excellence.
"""

from pepperpy.core.observability.base import (
    Counter,
    Gauge,
    Histogram,
    Metric,
    MetricsCollector,
    ObservabilityManager,
    Span,
    Tracer,
    create_observability_manager,
)

# Export public API
__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "Metric",
    "MetricsCollector",
    "ObservabilityManager",
    "Span",
    "Tracer",
    "create_observability_manager",
]
