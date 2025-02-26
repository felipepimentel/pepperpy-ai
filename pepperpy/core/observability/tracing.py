"""Tracing functionality.

This module provides tools for distributed tracing.
"""

import contextvars
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from pepperpy.core.observability.correlation import CorrelationManager


@dataclass
class TracingContext:
    """Context for a trace span."""

    name: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    context: dict[str, Any] = field(default_factory=dict)


# Global context variable
_tracing_context: contextvars.ContextVar[TracingContext | None] = (
    contextvars.ContextVar("tracing_context", default=None)
)


class Tracer:
    """Manages distributed tracing."""

    def __init__(self) -> None:
        """Initialize tracer."""
        self._correlation = CorrelationManager()

    def get_current_span(self) -> TracingContext | None:
        """Get current trace span.

        Returns:
            Current trace span or None
        """
        return _tracing_context.get()

    def set_span(
        self, span: TracingContext
    ) -> contextvars.Token[TracingContext | None]:
        """Set current trace span.

        Args:
            span: Span to set

        Returns:
            Token for resetting span
        """
        return _tracing_context.set(span)

    def reset_span(self, token: contextvars.Token[TracingContext | None]) -> None:
        """Reset trace span.

        Args:
            token: Token from set_span
        """
        _tracing_context.reset(token)

    @contextmanager
    def span(
        self, name: str, context: dict[str, Any] | None = None
    ) -> Generator[TracingContext, None, None]:
        """Create a new trace span.

        Args:
            name: Span name
            context: Optional span context

        Yields:
            New trace span
        """
        # Get parent span
        parent_span = self.get_current_span()
        parent_id = parent_span.span_id if parent_span else None

        # Create new span
        span = TracingContext(
            name=name,
            parent_id=parent_id,
            context=context or {},
        )

        # Set correlation ID
        correlation_id = self._correlation.get_correlation_id()
        if correlation_id:
            span.context["correlation_id"] = correlation_id

        # Set as current span
        token = self.set_span(span)
        try:
            yield span
        finally:
            # Record end time
            span.end_time = time.time()
            self.reset_span(token)

    def start_span(
        self, name: str, context: dict[str, Any] | None = None
    ) -> TracingContext:
        """Start a new trace span.

        Args:
            name: Span name
            context: Optional span context

        Returns:
            New trace span
        """
        # Get parent span
        parent_span = self.get_current_span()
        parent_id = parent_span.span_id if parent_span else None

        # Create new span
        span = TracingContext(
            name=name,
            parent_id=parent_id,
            context=context or {},
        )

        # Set correlation ID
        correlation_id = self._correlation.get_correlation_id()
        if correlation_id:
            span.context["correlation_id"] = correlation_id

        # Set as current span
        self.set_span(span)
        return span

    def end_span(self) -> None:
        """End the current trace span."""
        span = self.get_current_span()
        if span:
            span.end_time = time.time()
            _tracing_context.set(None)  # Simply clear the context


__all__ = ["Tracer", "TracingContext"]
