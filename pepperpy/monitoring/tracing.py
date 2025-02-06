"""Distributed tracing for the Pepperpy framework.

This module provides distributed tracing functionality using OpenTelemetry,
with support for span creation, context propagation, and trace sampling.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Span, Status, StatusCode

# Configure tracer provider
provider = TracerProvider(resource=Resource.create({"service.name": "pepperpy"}))

# Add console exporter for development
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

# Set global tracer provider
trace.set_tracer_provider(provider)

# Create tracer
tracer = trace.get_tracer(__name__)


class TracingManager:
    """Manager for distributed tracing operations."""

    def __init__(self) -> None:
        """Initialize tracing manager."""
        self.tracer = tracer

    @contextmanager
    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        kind: trace.SpanKind | None = None,
    ) -> Iterator[Span]:
        """Start a new span.

        Args:
            name: Name of the span.
            attributes: Optional span attributes.
            kind: Optional span kind.

        Yields:
            Span: The created span.
        """
        attributes = attributes or {}
        with self.tracer.start_as_current_span(
            name,
            attributes=attributes,
            kind=kind,
        ) as span:
            yield span

    def record_exception(
        self,
        span: Span,
        exception: Exception,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record an exception in a span.

        Args:
            span: The span to record the exception in.
            exception: The exception to record.
            attributes: Optional exception attributes.
        """
        attributes = attributes or {}
        span.record_exception(exception, attributes=attributes)
        span.set_status(Status(StatusCode.ERROR))

    def add_event(
        self,
        span: Span,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Add an event to a span.

        Args:
            span: The span to add the event to.
            name: Name of the event.
            attributes: Optional event attributes.
        """
        attributes = attributes or {}
        span.add_event(name, attributes=attributes)


# Create global tracing manager instance
tracing_manager = TracingManager()
