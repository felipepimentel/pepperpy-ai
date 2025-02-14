"""Type definitions for tracing."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SpanKind(Enum):
    """Types of spans."""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Status codes for spans."""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanContext:
    """Context for a tracing span.

    This class represents the context of a span in a trace.
    It contains information needed to correlate spans.

    Attributes:
        trace_id: Unique trace identifier
        span_id: Unique span identifier
        parent_id: Optional parent span identifier
        sampled: Whether this trace is sampled
        baggage: Optional baggage items

    """

    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    sampled: bool = True
    baggage: Dict[str, str] = field(default_factory=dict)


@dataclass
class SpanEvent:
    """An event within a span.

    Attributes:
        name: Event name
        timestamp: When the event occurred
        attributes: Event attributes

    """

    name: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """A tracing span.

    This class represents a single operation in a trace.
    It contains timing, context, and metadata about the operation.

    Attributes:
        name: Operation name
        context: Span context
        kind: Span kind
        start_time: When the span started
        end_time: When the span ended
        attributes: Span attributes
        events: Span events
        status: Operation status

    """

    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    status: SpanStatus = SpanStatus.UNSET

    def start(self) -> None:
        """Start the span."""
        self.start_time = datetime.utcnow()

    def end(self, end_time: Optional[datetime] = None) -> None:
        """End the span.

        Args:
            end_time: Optional end time

        """
        self.end_time = end_time or datetime.utcnow()

    def add_event(
        self,
        name: str,
        timestamp: Optional[datetime] = None,
        **attributes: Any,
    ) -> None:
        """Add an event to the span.

        Args:
            name: Event name
            timestamp: Optional event timestamp
            **attributes: Event attributes

        """
        event = SpanEvent(
            name=name,
            timestamp=timestamp or datetime.utcnow(),
            attributes=attributes,
        )
        self.events.append(event)

    def set_status(
        self,
        status: SpanStatus,
        description: Optional[str] = None,
    ) -> None:
        """Set the span status.

        Args:
            status: Status code
            description: Optional status description

        """
        self.status = status
        if description:
            self.attributes["status.description"] = description

    def record_exception(
        self,
        exception: Exception,
        timestamp: Optional[datetime] = None,
        **attributes: Any,
    ) -> None:
        """Record an exception.

        Args:
            exception: Exception to record
            timestamp: Optional timestamp
            **attributes: Additional attributes

        """
        self.add_event(
            name="exception",
            timestamp=timestamp,
            exception_type=exception.__class__.__name__,
            exception_message=str(exception),
            **attributes,
        )
        self.set_status(SpanStatus.ERROR, str(exception))
