"""Trace context management for distributed tracing.

This module provides context management for distributed tracing:
- Span context propagation
- Context carriers
- Context extraction and injection
"""

from typing import Any, Dict, Optional

from opentelemetry.trace import Span, SpanContext
from opentelemetry.trace.propagation.textmap import TextMapPropagator


class TraceContext:
    """Manages trace context for spans."""

    def __init__(self, span: Span) -> None:
        """Initialize trace context.

        Args:
            span: Active span

        """
        self.span = span
        self._context = span.get_span_context()

    @property
    def context(self) -> SpanContext:
        """Get span context.

        Returns:
            SpanContext: Current span context

        """
        return self._context

    def inject_context(self, carrier: Dict[str, str]) -> None:
        """Inject context into carrier.

        Args:
            carrier: Context carrier dictionary

        """
        propagator = TextMapPropagator()
        propagator.inject(carrier, self.context)

    @classmethod
    def extract_context(cls, carrier: Dict[str, str]) -> Optional[SpanContext]:
        """Extract context from carrier.

        Args:
            carrier: Context carrier dictionary

        Returns:
            Optional[SpanContext]: Extracted span context

        """
        propagator = TextMapPropagator()
        return propagator.extract(carrier)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to span.

        Args:
            name: Event name
            attributes: Optional event attributes

        """
        self.span.add_event(name, attributes=attributes or {})

    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute.

        Args:
            key: Attribute key
            value: Attribute value

        """
        self.span.set_attribute(key, value)

    def record_exception(self, exception: Exception) -> None:
        """Record exception in span.

        Args:
            exception: Exception to record

        """
        self.span.record_exception(exception)
