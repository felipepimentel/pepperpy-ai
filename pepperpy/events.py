"""Core event system for the Pepperpy framework.

This module provides the event system functionality for:
- Event bus implementation
- Event handlers and callbacks
- Event prioritization
- Event filtering
"""

import time
from datetime import datetime
from enum import Enum, IntEnum
from typing import (
    Any,
    Dict,
    Optional,
    Protocol,
    Set,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics import MetricsManager

# Configure logging
logger = logger.getChild(__name__)


class EventType(str, Enum):
    """Types of events in the system."""

    # System events
    SYSTEM = "system"
    SYSTEM_STARTED = "system.started"
    COMPONENT_CREATED = "system.component.created"

    # User events
    USER = "user"

    # Provider events
    PROVIDER = "provider"
    PROVIDER_REGISTERED = "provider.registered"
    PROVIDER_UNREGISTERED = "provider.unregistered"

    # Memory events
    MEMORY = "memory"

    # Agent events
    AGENT = "agent"
    AGENT_CREATED = "agent.created"
    AGENT_REMOVED = "agent.removed"


class EventPriority(IntEnum):
    """Event priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class Event(BaseModel):
    """Base event class for all events in the system."""

    id: UUID = Field(default_factory=uuid4)
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    source_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL


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


class EventMetrics:
    """Event metrics collector."""

    def __init__(self):
        """Initialize event metrics."""
        self._metrics_manager = MetricsManager.get_instance()
        self._events_counter = None
        self._latency_gauge = None

    async def initialize(self):
        """Initialize metrics."""
        self._events_counter = await self._metrics_manager.create_counter(
            "events_processed",
            "Total number of events processed",
            labels={"type": "event"},
        )
        self._latency_gauge = await self._metrics_manager.create_gauge(
            "event_latency",
            "Event processing latency in seconds",
            labels={"type": "event"},
        )

    def record_event(self):
        """Record event processing."""
        if self._events_counter is not None:
            self._events_counter.record(1)

    def record_latency(self, latency: float):
        """Record event processing latency."""
        if self._latency_gauge is not None:
            self._latency_gauge.record(latency)

    def record_metric(self, name: str, value: float):
        """Record a metric value."""
        metric = self._metrics_manager.get_metric(name)
        if metric is not None:
            metric.record(value)


# Initialize metrics manager
metrics = EventMetrics()


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
