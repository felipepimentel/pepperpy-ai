"""Tracing module for distributed tracing support."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from .errors import ContextError as ContextError
from .errors import SpanError
from .errors import TracingError as TracingError


@dataclass
class SpanContext:
    """Context for a tracing span."""

    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)


@dataclass
class Span:
    """Represents a single operation within a trace."""

    name: str
    context: SpanContext
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "OK"
    kind: str = "INTERNAL"

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": datetime.now(UTC).isoformat(),
            "attributes": attributes or {},
        })

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def end(self) -> None:
        """End the span."""
        self.end_time = datetime.now(UTC)


class TracingManager:
    """Manages tracing operations.

    This class provides functionality for:
    - Creating and managing spans
    - Propagating context
    - Exporting traces
    """

    def __init__(self) -> None:
        """Initialize the tracing manager."""
        self._active_spans: Dict[str, Span] = {}

    def create_span(
        self,
        name: str,
        context: Optional[SpanContext] = None,
        kind: str = "INTERNAL",
    ) -> Span:
        """Create a new span.

        Args:
            name: Span name
            context: Optional parent context
            kind: Span kind (INTERNAL, CLIENT, SERVER, etc.)

        Returns:
            Created span

        Raises:
            SpanError: If span creation fails

        """
        try:
            # In a real implementation, we would generate proper trace and span IDs
            span = Span(
                name=name,
                context=context or SpanContext(trace_id="trace-1", span_id="span-1"),
                kind=kind,
            )
            self._active_spans[span.context.span_id] = span
            return span
        except Exception as e:
            raise SpanError(f"Failed to create span: {e}")

    def end_span(self, span: Span) -> None:
        """End a span.

        Args:
            span: Span to end

        Raises:
            SpanError: If ending the span fails

        """
        try:
            span.end()
            self._active_spans.pop(span.context.span_id, None)
        except Exception as e:
            raise SpanError(f"Failed to end span: {e}")

    def get_active_span(self, span_id: str) -> Optional[Span]:
        """Get an active span by ID.

        Args:
            span_id: Span ID to retrieve

        Returns:
            Span if found, None otherwise

        """
        return self._active_spans.get(span_id)

    def clear(self) -> None:
        """Clear all active spans."""
        self._active_spans.clear()
