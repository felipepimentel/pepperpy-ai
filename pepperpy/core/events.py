"""Core event system for the Pepperpy framework.

This module provides the event system functionality for:
- Event bus implementation
- Event handlers and callbacks
- Event prioritization
- Event filtering
"""

import asyncio
import time
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Dict,
    ForwardRef,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)
from uuid import UUID, uuid4

import aiofiles
import aiofiles.os
from pydantic import BaseModel, Field, field_validator

from pepperpy.core.enums import MetricType
from pepperpy.core.exceptions import ValidationError
from pepperpy.monitoring import logger, metrics

T = TypeVar("T")
Event = ForwardRef("Event")


class EventType(str, Enum):
    """Types of events in the system."""

    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    SYSTEM_ERROR = "system_error"

    # Provider events
    PROVIDER_REGISTERED = "provider_registered"
    PROVIDER_UNREGISTERED = "provider_unregistered"
    PROVIDER_ERROR = "provider_error"

    # Agent events
    AGENT_CREATED = "agent_created"
    AGENT_REMOVED = "agent_removed"
    AGENT_ERROR = "agent_error"

    # Component events
    COMPONENT_CREATED = "component_created"
    COMPONENT_REMOVED = "component_removed"
    COMPONENT_ERROR = "component_error"

    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Memory events
    MEMORY_STORED = "memory_stored"
    MEMORY_RETRIEVED = "memory_retrieved"
    MEMORY_CLEARED = "memory_cleared"

    # Metric events
    METRIC_RECORDED = "metric_recorded"
    METRIC_CLEARED = "metric_cleared"


class EventPriority(str, Enum):
    """Event priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EventMetrics:
    """Metrics for event processing.

    Attributes
    ----------
        processed_count: Number of events processed
        error_count: Number of processing errors
        avg_processing_time: Average processing time in seconds
        last_event_time: Timestamp of last processed event

    """

    processed_count: int = 0
    error_count: int = 0
    avg_processing_time: float = 0.0
    last_event_time: float = 0.0

    def update(self, processing_time: float, success: bool = True) -> None:
        """Update metrics with new event processing data."""
        self.processed_count += 1
        if not success:
            self.error_count += 1
        self.avg_processing_time = (
            self.avg_processing_time * (self.processed_count - 1) + processing_time
        ) / self.processed_count
        self.last_event_time = time.time()


@runtime_checkable
class EventFilter(Protocol):
    """Protocol for event filters."""

    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria.

        Args:
        ----
            event: Event to check

        Returns:
        -------
            True if event matches criteria, False otherwise

        """
        ...


class Event(BaseModel):
    """Base event model.

    Attributes
    ----------
        id: Unique event identifier
        type: Type of event
        source_id: Identifier of event source
        priority: Event priority level
        timestamp: Event creation time
        data: Event payload data

    """

    id: UUID = Field(default_factory=uuid4)
    type: EventType
    source_id: str
    priority: EventPriority = Field(default=EventPriority.MEDIUM)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=lambda: {})

    class Config:
        """Pydantic model configuration."""

        frozen = True
        json_encoders: ClassVar[dict[type, Callable]] = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
            EventType: lambda v: v.name,
            EventPriority: lambda v: v.name,
        }

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, v: str) -> str:
        """Validate source_id is not empty."""
        if not v.strip():
            raise ValueError("source_id cannot be empty")
        return v

    @field_validator("data")
    @classmethod
    def validate_dict(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure dictionaries are immutable."""
        return dict(v)

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return self.json()

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create event from JSON string.

        Args:
        ----
            json_str: JSON string representation of event

        Returns:
        -------
            Event instance

        """
        return cls.parse_raw(json_str)


class EventBuffer(Generic[T]):
    """Buffer for batching events.

    Attributes
    ----------
        max_size: Maximum number of events to buffer
        flush_interval: Time interval for automatic flush

    """

    def __init__(
        self,
        max_size: int = 100,
        flush_interval: float = 1.0,
        on_flush: Callable[[list[T]], None] | None = None,
    ) -> None:
        """Initialize the buffer.

        Args:
        ----
            max_size: Maximum number of events to buffer
            flush_interval: Time interval for automatic flush in seconds
            on_flush: Callback function when buffer is flushed

        """
        self.max_size = max_size
        self.flush_interval = flush_interval
        self.on_flush = on_flush
        self._buffer: list[T] = []
        self._last_flush = time.time()

    def add(self, item: T) -> None:
        """Add item to buffer."""
        self._buffer.append(item)
        if len(self._buffer) >= self.max_size or self._should_flush():
            self.flush()

    def flush(self) -> None:
        """Flush buffer contents."""
        if self._buffer and self.on_flush:
            self.on_flush(self._buffer)
        self._buffer.clear()
        self._last_flush = time.time()

    def _should_flush(self) -> bool:
        """Check if buffer should be flushed based on time."""
        return time.time() - self._last_flush >= self.flush_interval


class EventFilterImpl:
    """Implementation of the EventFilter protocol.

    Attributes
    ----------
        source_ids: Optional list of source IDs to filter by
        event_types: Optional list of event types to filter by
        time_window: Optional time window (start, end) to filter by
        custom_filter: Optional custom filter function

    """

    def __init__(
        self,
        source_ids: list[str] | None = None,
        event_types: list[EventType] | None = None,
        time_window: tuple[datetime, datetime] | None = None,
        custom_filter: Callable[[Event], bool] | None = None,
    ) -> None:
        """Initialize event filter.

        Args:
        ----
            source_ids: Optional list of source IDs to filter by
            event_types: Optional list of event types to filter by
            time_window: Optional time window (start, end) to filter by
            custom_filter: Optional custom filter function

        """
        self.source_ids = source_ids
        self.event_types = event_types
        self.time_window = time_window
        self.custom_filter = custom_filter

    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria.

        Args:
        ----
            event: Event to check

        Returns:
        -------
            True if event matches criteria, False otherwise

        """
        if self.source_ids and event.source_id not in self.source_ids:
            return False
        if self.event_types and event.type not in self.event_types:
            return False
        if self.time_window:
            start, end = self.time_window
            if not (start <= event.timestamp <= end):
                return False
        if self.custom_filter and not self.custom_filter(event):
            return False
        return True


class EventStore:
    """Event storage and retrieval.

    Attributes
    ----------
        storage_path: Path to event storage directory

    """

    def __init__(self, storage_path: str | None = None):
        """Initialize event store.

        Args:
        ----
            storage_path: Optional path to event storage directory

        """
        self._events: list[Event] = []
        if storage_path:
            self._storage_path = Path(storage_path)
            self._storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self._storage_path = None

    async def store_event(self, event: Event) -> None:
        """Store an event.

        Args:
        ----
            event: Event to store

        """
        path = self._storage_path / f"{event.id}.json"
        async with aiofiles.open(path, "w") as f:
            await f.write(event.to_json())

    async def get_event(self, event_id: UUID) -> Event | None:
        """Retrieve an event by ID.

        Args:
        ----
            event_id: ID of event to retrieve

        Returns:
        -------
            Event if found, None otherwise

        """
        path = self._storage_path / f"{event_id}.json"
        try:
            async with aiofiles.open(path) as f:
                data = await f.read()
                return Event.from_json(data)
        except FileNotFoundError:
            return None

    async def get_events(
        self,
        source_ids: list[str] | None = None,
        event_types: list[EventType] | None = None,
        time_window: tuple[datetime, datetime] | None = None,
        custom_filter: Callable[[Event], bool] | None = None,
    ) -> list[Event]:
        """Get events matching filter criteria.

        Args:
        ----
            source_ids: Optional list of source IDs to filter by
            event_types: Optional list of event types to filter by
            time_window: Optional time window (start, end) to filter by
            custom_filter: Optional custom filter function

        Returns:
        -------
            List of matching events

        """
        events = []
        for event in self._events:
            if source_ids and event.source_id not in source_ids:
                continue
            if event_types and event.type not in event_types:
                continue
            if time_window:
                start, end = time_window
                if not (start <= event.timestamp <= end):
                    continue
            if custom_filter and not custom_filter(event):
                continue
            events.append(event)
        return events


class EventHandler(Protocol):
    """Protocol for event handlers."""

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Handle an event.

        Args:
        ----
            event: Event to handle

        """
        pass


class CompositeEvent(Event):
    """Represents a composite event made up of multiple sub-events.

    Attributes
    ----------
        sub_events: List of sub-events that make up this composite event
        completion_criteria: Function that determines when composite event is complete
        timeout: Optional timeout for composite event completion

    """

    sub_events: list[Event] = Field(default_factory=list)
    completion_criteria: Callable[[list[Event]], bool] | None = None
    timeout: float | None = None

    def is_complete(self) -> bool:
        """Check if composite event is complete."""
        if not self.completion_criteria:
            return len(self.sub_events) > 0
        return self.completion_criteria(self.sub_events)


class EventCorrelator:
    """Correlates events based on patterns to detect complex event sequences."""

    def __init__(
        self,
        patterns: list[dict[str, Any]],
        window_size: timedelta = timedelta(minutes=5),
        min_confidence: float = 0.8,
    ) -> None:
        """Initialize event correlator.

        Args:
        ----
            patterns: List of event patterns to match
            window_size: Time window for correlation
            min_confidence: Minimum confidence threshold

        """
        self.patterns = patterns
        self.window_size = window_size
        self.min_confidence = min_confidence
        self.events: list[Event] = []
        self._cleanup_task: asyncio.Task | None = None

    def add_event(self, event: Event) -> list[CompositeEvent]:
        """Add event and check for pattern matches.

        Args:
        ----
            event: Event to add

        Returns:
        -------
            List of detected composite events

        """
        now = datetime.utcnow()
        cutoff = now - self.window_size

        # Remove old events
        self.events = [e for e in self.events if e.timestamp >= cutoff]

        # Add new event
        self.events.append(event)

        # Check for pattern matches
        composite_events: list[CompositeEvent] = []
        for pattern in self.patterns:
            if self._matches_pattern(pattern):
                composite_events.append(self._create_composite_event(pattern))

        return composite_events

    def _matches_pattern(self, pattern: dict[str, Any]) -> bool:
        """Check if current window matches pattern."""
        # Pattern matching logic here
        return False

    def _create_composite_event(self, pattern: dict[str, Any]) -> CompositeEvent:
        """Create composite event from matched pattern."""
        return CompositeEvent(
            type=EventType.SYSTEM_STARTED,  # Using a valid event type
            source_id="correlator",
            sub_events=self.events.copy(),
        )


class EventBus:
    """Event bus for managing event subscriptions and delivery."""

    def __init__(self) -> None:
        """Initialize event bus."""
        self.event_store: Optional["EventStore"] = None
        self.correlator: Optional["EventCorrelator"] = None
        self._handlers: Dict[EventType, set[EventHandler]] = {}
        self._filters: Dict[EventHandler, set[EventFilter]] = {}
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._metrics = EventMetrics()

    async def _setup_monitoring(self) -> None:
        """Setup monitoring for the event bus."""
        await metrics.record_metric(
            name="event_bus_queue_size",
            value=0,
            metric_type=MetricType.GAUGE,
            labels={"bus_id": str(id(self))},
        )
        await metrics.record_metric(
            name="event_bus_processed_count",
            value=0,
            metric_type=MetricType.COUNTER,
            labels={"bus_id": str(id(self))},
        )
        await metrics.record_metric(
            name="event_bus_error_count",
            value=0,
            metric_type=MetricType.COUNTER,
            labels={"bus_id": str(id(self))},
        )

    @property
    def is_active(self) -> bool:
        """Whether the event bus is active."""
        return self._running

    @property
    def metrics(self) -> EventMetrics:
        """Get event bus metrics."""
        return self._metrics

    async def start(self) -> None:
        """Start the event bus."""
        if self._running:
            raise ValidationError("Event bus already started")
        self._running = True
        await self._setup_monitoring()
        logger.info("Event bus started", extra={})

    async def stop(self) -> None:
        """Stop the event bus."""
        if not self._running:
            raise ValidationError("Event bus not started")
        self._running = False
        logger.info("Event bus stopped", extra={})

    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                event = await self._queue.get()
                start_time = time.time()
                success = True

                try:
                    await self._dispatch_event(event)
                except Exception as e:
                    success = False
                    logger.error(
                        "Failed to dispatch event",
                        extra={
                            "event_id": str(event.id),
                            "error": str(e),
                        },
                    )

                # Update metrics
                self._metrics.update(
                    time.time() - start_time,
                    success=success,
                )

                self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Event processing error",
                    extra={"error": str(e)},
                )

    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch event to handlers.

        Args:
        ----
            event: Event to dispatch

        """
        # Store event if we have a store
        if self.event_store:
            try:
                await self.event_store.store_event(event)
            except Exception as e:
                logger.error(
                    "Failed to store event",
                    extra={
                        "event_id": str(event.id),
                        "error": str(e),
                    },
                )

        # Check for patterns if we have a correlator
        if self.correlator:
            try:
                composite_events = self.correlator.add_event(event)
                for composite_event in composite_events:
                    await self.publish(composite_event)
            except Exception as e:
                logger.error(
                    "Failed to correlate event",
                    extra={
                        "event_id": str(event.id),
                        "error": str(e),
                    },
                )

        # Dispatch to handlers
        for handler in self._handlers.get(event.type, set()):
            # Check filters
            if handler in self._filters:
                if not any(f.matches(event) for f in self._filters[handler]):
                    continue

            try:
                await handler.handle_event(event)
            except Exception as e:
                logger.error(
                    "Handler failed to process event",
                    extra={
                        "handler_id": str(id(handler)),
                        "event_id": str(event.id),
                        "error": str(e),
                    },
                )

    def subscribe(
        self,
        handler: EventHandler,
        event_type: EventType | None = None,
        filters: list[EventFilter] | None = None,
    ) -> None:
        """Subscribe to events.

        Args:
        ----
            handler: Event handler
            event_type: Optional specific event type to subscribe to
            filters: Optional event filters

        """
        if event_type:
            if event_type not in self._handlers:
                self._handlers[event_type] = set()
            self._handlers[event_type].add(handler)
        else:
            # Subscribe to all event types
            for evt_type in EventType:
                if evt_type not in self._handlers:
                    self._handlers[evt_type] = set()
                self._handlers[evt_type].add(handler)

        if filters:
            if handler not in self._filters:
                self._filters[handler] = set()
            self._filters[handler].update(filters)

    def unsubscribe(
        self,
        handler: EventHandler,
        event_type: EventType | None = None,
    ) -> None:
        """Unsubscribe from events.

        Args:
        ----
            handler: Event handler to unsubscribe
            event_type: Optional specific event type to unsubscribe from

        """
        if event_type:
            if event_type in self._handlers:
                self._handlers[event_type].discard(handler)
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
        else:
            # Unsubscribe from all event types
            for handlers in self._handlers.values():
                handlers.discard(handler)
            # Clean up empty handler sets
            self._handlers = {
                evt_type: handlers
                for evt_type, handlers in self._handlers.items()
                if handlers
            }

        # Remove filters
        if handler in self._filters:
            del self._filters[handler]

    async def publish(
        self,
        event: Event,
        correlation_id: UUID | None = None,
        parent_id: UUID | None = None,
        priority: int | None = None,
    ) -> None:
        """Publish an event.

        Args:
        ----
            event: Event to publish
            correlation_id: Optional correlation ID
            parent_id: Optional parent event ID
            priority: Optional priority override

        """
        # Update event metadata
        event_data = event.dict()
        if correlation_id:
            event_data["correlation_id"] = correlation_id
        if parent_id:
            event_data["parent_id"] = parent_id
        if priority is not None:
            event_data["priority"] = EventPriority(priority)

        # Create new event with updated metadata
        new_event = Event(**event_data)

        # Add to queue
        await self._queue.put(new_event)

    async def get_correlated_events(self, correlation_id: str) -> list[Event]:
        """Get events with matching correlation ID.

        Args:
        ----
            correlation_id: Correlation ID to match

        Returns:
        -------
            List of events with matching correlation ID

        Raises:
        ------
            ValueError: If correlation_id is empty

        """
        if not correlation_id.strip():
            raise ValueError("correlation_id cannot be empty")

        events = []
        for event in self._events:
            if event.data.get("correlation_id") == correlation_id:
                events.append(event)
        return events


async def create_event_bus(
    event_store: Optional["EventStore"] = None,
    correlator: Optional["EventCorrelator"] = None,
    event_handlers: Optional[Dict[EventType, set[EventHandler]]] = None,
    max_queue_size: int = 1000,
) -> EventBus:
    """Create and initialize a new event bus instance.

    Args:
    ----
        event_store: Optional event store for persistence
        correlator: Optional event correlator for pattern matching
        event_handlers: A dictionary mapping event types to a list of event handlers
        max_queue_size: The maximum size of the event queue

    Returns:
    -------
        EventBus: A new initialized event bus instance

    """
    bus = EventBus()
    bus.event_store = event_store
    bus.correlator = correlator
    bus._handlers = event_handlers or {}
    bus._queue = asyncio.Queue(maxsize=max_queue_size)
    bus._running = False
    bus._task = None
    await bus._setup_monitoring()
    return bus


# Initialize the default event bus
event_bus = asyncio.run(
    create_event_bus(
        correlator=EventCorrelator(
            patterns=[
                # Add default patterns here
            ]
        )
    )
)


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
        ----
            event_type: Type of event
            data: Optional event data

        """
        self._event_count += 1
        await metrics.record_metric(
            "events_total",
            self._event_count,
            MetricType.COUNTER,
            {"type": event_type},
        )

    async def emit_error(
        self, error_type: str, error: Exception, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit an error event.

        Args:
        ----
            error_type: Type of error
            error: The error that occurred
            data: Optional error data

        """
        self._error_count += 1
        await metrics.record_metric(
            "errors_total",
            self._error_count,
            MetricType.COUNTER,
            {"type": error_type},
        )

    async def emit_warning(
        self, warning_type: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit a warning event.

        Args:
        ----
            warning_type: Type of warning
            message: Warning message
            data: Optional warning data

        """
        self._warning_count += 1
        await metrics.record_metric(
            "warnings_total",
            self._warning_count,
            MetricType.COUNTER,
            {"type": warning_type},
        )


# Global event emitter instance
event_emitter = EventEmitter()
