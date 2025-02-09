"""Distributed tracing for the Pepperpy framework.

This module provides distributed tracing functionality using OpenTelemetry,
with support for span creation, context propagation, and trace sampling.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.util.types import Attributes

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
        attributes: Attributes | None = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    ) -> Iterator[Span]:
        """Start a new span.

        Args:
            name: Name of the span.
            attributes: Optional span attributes.
            kind: Optional span kind.

        Yields:
            Span: The created span.
        """
        with self.tracer.start_as_current_span(
            name,
            attributes=attributes or {},
            kind=kind,
        ) as span:
            yield span

    def record_exception(
        self,
        span: Span,
        exception: Exception,
        attributes: Attributes | None = None,
    ) -> None:
        """Record an exception in a span.

        Args:
            span: The span to record the exception in.
            exception: The exception to record.
            attributes: Optional exception attributes.
        """
        span.record_exception(exception, attributes=attributes or {})
        span.set_status(Status(StatusCode.ERROR))

    def add_event(
        self,
        span: Span,
        name: str,
        attributes: Attributes | None = None,
    ) -> None:
        """Add an event to a span.

        Args:
            span: The span to add the event to.
            name: Name of the event.
            attributes: Optional event attributes.
        """
        span.add_event(name, attributes=attributes or {})


# Create global tracing manager instance
tracing_manager = TracingManager()
