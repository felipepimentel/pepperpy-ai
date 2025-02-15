"""Centralized tracing system.

This module provides a unified tracing interface with support for distributed
tracing, span management, and context propagation. It integrates with OpenTelemetry
for standardized tracing.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.monitoring.logging import get_logger
from pepperpy.core.monitoring.types import MonitoringError

__all__ = [
    "Span",
    "SpanContext",
    "TracingError",
    "TracingManager",
    "trace_span",
]


class TracingError(MonitoringError):
    """Error raised by tracing operations."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            details: Additional error details

        """
        super().__init__(message, "TRACING_ERROR", details)


class SpanContext:
    """Context information for a tracing span."""

    def __init__(
        self,
        trace_id: str,
        span_id: str,
        trace_flags: Optional[int] = None,
        trace_state: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize the span context.

        Args:
            trace_id: Trace ID
            span_id: Span ID
            trace_flags: Optional trace flags
            trace_state: Optional trace state

        """
        self.trace_id = trace_id
        self.span_id = span_id
        self.trace_flags = trace_flags
        self.trace_state = trace_state or {}


class TracingManager(Lifecycle):
    """Central manager for distributed tracing.

    This class provides a unified interface for creating and managing traces
    across the application, with support for context propagation and span
    management.
    """

    def __init__(self) -> None:
        """Initialize the tracing manager."""
        super().__init__()
        self._tracer = trace.get_tracer(__name__)
        self._propagator = TraceContextTextMapPropagator()
        self._logger = get_logger(__name__)

    async def initialize(self) -> None:
        """Initialize the tracing manager."""
        self._logger.info("Initializing tracing manager")

    async def cleanup(self) -> None:
        """Clean up tracing resources."""
        self._logger.info("Cleaning up tracing manager")

    @asynccontextmanager
    async def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        links: Optional[Dict[str, str]] = None,
    ) -> AsyncGenerator[Span, None]:
        """Create and manage a tracing span.

        Args:
            name: Name of the span
            kind: Kind of span (default: INTERNAL)
            attributes: Optional span attributes
            links: Optional links to other spans

        Yields:
            Active span instance

        Example:
            ```python
            async with tracing_manager.span("process_request") as span:
                span.set_attribute("request.id", request_id)
                result = await process_request()
                span.set_attribute("response.status", result.status)
            ```

        """
        with self._tracer.start_as_current_span(
            name,
            kind=kind,
            attributes=attributes,
        ) as span:
            try:
                if links:
                    for key, value in links.items():
                        span.add_link(value, attributes={key: value})

                self._logger.debug(
                    "Started span",
                    span_name=name,
                    span_id=span.get_span_context().span_id,
                    trace_id=span.get_span_context().trace_id,
                )

                yield span

                # Set success status if no exception occurred
                span.set_status(Status(StatusCode.OK))

            except Exception as e:
                # Set error status and record exception
                span.set_status(
                    Status(StatusCode.ERROR, str(e)),
                    attributes={"error.type": e.__class__.__name__},
                )
                span.record_exception(e)
                raise

            finally:
                self._logger.debug(
                    "Ended span",
                    span_name=name,
                    span_id=span.get_span_context().span_id,
                    trace_id=span.get_span_context().trace_id,
                )

    def inject_context(self, carrier: Dict[str, str]) -> None:
        """Inject current trace context into carrier.

        This is used to propagate trace context across service boundaries.

        Args:
            carrier: Dictionary to inject context into

        """
        self._propagator.inject(carrier)

    def extract_context(self, carrier: Dict[str, str]) -> trace.Context:
        """Extract trace context from carrier.

        This is used to continue traces across service boundaries.

        Args:
            carrier: Dictionary containing trace context

        Returns:
            Extracted trace context

        """
        return self._propagator.extract(carrier)


# Global tracing manager instance
tracing_manager = TracingManager()


@asynccontextmanager
async def trace_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None,
    links: Optional[Dict[str, str]] = None,
) -> AsyncGenerator[Span, None]:
    """Create a tracing span using the global tracing manager.

    This is a convenience function that uses the global tracing manager.

    Args:
        name: Name of the span
        kind: Kind of span (default: INTERNAL)
        attributes: Optional span attributes
        links: Optional links to other spans

    Yields:
        Active span instance

    """
    async with tracing_manager.span(name, kind, attributes, links) as span:
        yield span
