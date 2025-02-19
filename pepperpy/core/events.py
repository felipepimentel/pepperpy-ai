"""Core event system for the Pepperpy framework.

This module provides the event system functionality for:
- Event bus implementation
- Event handlers and callbacks
- Event prioritization
- Event filtering
"""

import time
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Dict,
    Optional,
    Protocol,
    Set,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.logging import get_logger
from pepperpy.core.metrics import Counter, Gauge, MetricConfig, MetricValue

# Configure logging
logger = get_logger(__name__)


class EventType(str, Enum):
    """Types of events in the system."""

    SYSTEM = "system"
    USER = "user"
    PROVIDER = "provider"
    MEMORY = "memory"
    AGENT = "agent"


class Event(BaseModel):
    """Base event class for all events in the system."""

    id: UUID = Field(default_factory=uuid4)
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)


class EventHandler(Protocol):
    """Protocol for event handlers."""

    async def handle_event(self, event: Event) -> None:
        """Handle an event."""
        ...


class EventFilter(Protocol):
    """Protocol for event filters."""

    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria."""
        ...


class MetricsManager:
    """Manages metrics for the event system."""

    def __init__(self):
        self._event_counter = Counter(
            MetricConfig(
                name="events_processed",
                description="Number of events processed",
                unit="count",
            )
        )
        self._event_latency = Gauge(
            MetricConfig(
                name="event_latency",
                description="Event processing latency",
                unit="seconds",
            )
        )
        self._metrics: Dict[str, Counter | Gauge] = {
            "events_processed": self._event_counter,
            "event_latency": self._event_latency,
        }

    def record_event(self):
        """Record an event being processed."""
        self._event_counter.record(1)

    def record_latency(self, latency: float):
        """Record event processing latency."""
        self._event_latency.record(latency)

    def record_metric(self, name: str, value: MetricValue):
        """Record a metric value."""
        if name in self._metrics:
            self._metrics[name].record(value)
        else:
            logger.warning(f"Metric {name} not found")


# Initialize metrics manager
metrics = MetricsManager()


class EventBus:
    """Event bus implementation."""

    def __init__(self):
        """Initialize the event bus."""
        self._events: Dict[UUID, Event] = {}
        self._handlers: Dict[EventType, Set[EventHandler]] = {}
        self._filters: Dict[EventType, Set[EventFilter]] = {}

    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
        filter_: Optional[EventFilter] = None,
    ):
        """Subscribe to events of a specific type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = set()
        self._handlers[event_type].add(handler)

        if filter_ is not None:
            if event_type not in self._filters:
                self._filters[event_type] = set()
            self._filters[event_type].add(filter_)

    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ):
        """Unsubscribe from events of a specific type."""
        if event_type in self._handlers:
            self._handlers[event_type].discard(handler)

    async def publish(self, event: Event):
        """Publish an event to all subscribed handlers."""
        self._events[event.id] = event
        metrics.record_event()

        start_time = time.time()

        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                filters = self._filters.get(event.type, set())
                if not filters or any(f.matches(event) for f in filters):
                    try:
                        await handler.handle_event(event)
                    except Exception as e:
                        logger.error(f"Error handling event {event.id}: {e}")

        metrics.record_latency(time.time() - start_time)


class EventEmitter:
    """Event emitter for tracking and emitting events."""

    def __init__(self) -> None:
        """Initialize the event emitter."""
        self._event_count = 0
        self._error_count = 0
        self._warning_count = 0

    async def emit(
        self, event_type: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit an event.

        Args:
            event_type: Type of event
            data: Optional event data
        """
        self._event_count += 1
        metrics.record_metric("events_total", self._event_count)

    async def emit_error(
        self, error_type: str, error: Exception, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit an error event.

        Args:
            error_type: Type of error
            error: The error that occurred
            data: Optional error data
        """
        self._error_count += 1
        metrics.record_metric("errors_total", self._error_count)

    async def emit_warning(
        self, warning_type: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit a warning event.

        Args:
            warning_type: Type of warning
            message: Warning message
            data: Optional warning data
        """
        self._warning_count += 1
        metrics.record_metric("warnings_total", self._warning_count)


# Global event emitter instance
event_emitter = EventEmitter()
