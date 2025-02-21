"""Core event system for the Pepperpy framework.

This module provides the event system functionality for:
- Event bus implementation
- Event handlers and callbacks
- Event prioritization
- Event filtering
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, IntEnum
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    TypeVar,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.base import Lifecycle
from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager

# Configure logging
logger = logger.getChild(__name__)

# Type variables for generic event handling
T_Event = TypeVar("T_Event", bound="Event")
T_Handler = TypeVar("T_Handler", bound="EventHandler")


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
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    MEMORY_UPDATED = "memory.updated"

    # Agent events
    AGENT = "agent"
    AGENT_CREATED = "agent.created"
    AGENT_REMOVED = "agent.removed"
    AGENT_STATE_CHANGED = "agent.state.changed"

    # Workflow events
    WORKFLOW = "workflow"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Hub events
    HUB = "hub"
    HUB_ASSET_CREATED = "hub.asset.created"
    HUB_ASSET_UPDATED = "hub.asset.updated"
    HUB_ASSET_DELETED = "hub.asset.deleted"


class EventPriority(IntEnum):
    """Event priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class EventMetadata(BaseModel):
    """Base class for event metadata."""

    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_id: UUID = Field(default_factory=uuid4)
    priority: EventPriority = Field(default=EventPriority.NORMAL)
    metadata: Dict[str, Any] = {}


class Event:
    """Base class for all events."""

    def __init__(
        self,
        event_type: str,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize event.

        Args:
            event_type: Type of event
            priority: Event priority level
            metadata: Optional event metadata
        """
        self._event_metadata = EventMetadata(
            event_type=event_type, priority=priority, metadata=metadata or {}
        )

    @property
    def event_type(self) -> str:
        """Get event type."""
        return self._event_metadata.event_type

    @property
    def event_id(self) -> UUID:
        """Get event ID."""
        return self._event_metadata.event_id

    @property
    def timestamp(self) -> datetime:
        """Get event timestamp."""
        return self._event_metadata.timestamp

    @property
    def priority(self) -> EventPriority:
        """Get event priority."""
        return self._event_metadata.priority

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get event metadata."""
        return self._event_metadata.metadata


class EventHandler(ABC, Generic[T_Event]):
    """Base class for event handlers.

    Attributes:
        priority: Handler priority level
        event_types: List of supported event types
    """

    def __init__(self, priority: EventPriority = EventPriority.NORMAL) -> None:
        """Initialize event handler.

        Args:
            priority: Handler priority level
        """
        self._priority = priority
        self._event_types: List[str] = []

    @property
    def priority(self) -> EventPriority:
        """Get handler priority."""
        return self._priority

    @abstractmethod
    async def handle_event(self, event: T_Event) -> None:
        """Handle an event.

        Args:
            event: Event to handle
        """
        pass

    @property
    def supported_event_types(self) -> List[str]:
        """Get list of supported event types.

        Returns:
            List of event types this handler can process
        """
        return self._event_types

    def supports_event_type(self, event_type: str) -> bool:
        """Check if handler supports an event type.

        Args:
            event_type: Event type to check

        Returns:
            bool: True if event type is supported
        """
        return event_type in self._event_types or not self._event_types


class EventFilter(Protocol):
    """Protocol for event filters."""

    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria.

        Args:
            event: Event to check

        Returns:
            bool: True if event matches criteria
        """
        ...


class EventTypeFilter:
    """Filter events by type."""

    def __init__(self, allowed_types: List[str]) -> None:
        """Initialize filter.

        Args:
            allowed_types: List of allowed event types
        """
        self._allowed_types = allowed_types

    def matches(self, event: Event) -> bool:
        """Check if event type is allowed.

        Args:
            event: Event to check

        Returns:
            bool: True if event type is allowed
        """
        return event.event_type in self._allowed_types


class PriorityFilter:
    """Filter events by priority."""

    def __init__(self, min_priority: EventPriority) -> None:
        """Initialize filter.

        Args:
            min_priority: Minimum priority level
        """
        self._min_priority = min_priority

    def matches(self, event: Event) -> bool:
        """Check if event priority meets minimum.

        Args:
            event: Event to check

        Returns:
            bool: True if event priority is sufficient
        """
        return event.priority >= self._min_priority


class EventMetrics:
    """Metrics tracking for the event system."""

    def __init__(self) -> None:
        """Initialize event metrics."""
        self._metrics = MetricsManager.get_instance()
        self._event_counters: Dict[str, Counter] = {}
        self._error_counters: Dict[str, Counter] = {}
        self._latency_histograms: Dict[str, Histogram] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize metrics collection.

        This method must be called before using any metrics.
        """
        if self._initialized:
            return

        self._initialized = True
        logger.debug("Event metrics initialized")

    async def _ensure_event_counter(self, event_type: str) -> Counter:
        """Ensure counter exists for event type.

        Args:
            event_type: Type of event

        Returns:
            Counter for event type
        """
        if event_type not in self._event_counters:
            self._event_counters[event_type] = await self._metrics.create_counter(
                f"events_total_{event_type}",
                f"Total number of {event_type} events processed",
                labels={"event_type": event_type},
            )
        return self._event_counters[event_type]

    async def _ensure_error_counter(self, event_type: str) -> Counter:
        """Ensure error counter exists for event type.

        Args:
            event_type: Type of event

        Returns:
            Error counter for event type
        """
        if event_type not in self._error_counters:
            self._error_counters[event_type] = await self._metrics.create_counter(
                f"errors_total_{event_type}",
                f"Total number of {event_type} event errors",
                labels={"event_type": event_type},
            )
        return self._error_counters[event_type]

    async def _ensure_latency_histogram(self, event_type: str) -> Histogram:
        """Ensure latency histogram exists for event type.

        Args:
            event_type: Type of event

        Returns:
            Latency histogram for event type
        """
        if event_type not in self._latency_histograms:
            self._latency_histograms[event_type] = await self._metrics.create_histogram(
                f"event_processing_duration_seconds_{event_type}",
                f"Event processing duration in seconds for {event_type} events",
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
                labels={"event_type": event_type},
            )
        return self._latency_histograms[event_type]

    async def record_event(self, event_type: str) -> None:
        """Record an event occurrence.

        Args:
            event_type: Type of event
        """
        if not self._initialized:
            logger.warning("Metrics not initialized")
            return

        counter = await self._ensure_event_counter(event_type)
        counter.record(1)

    async def record_error(self, event_type: str) -> None:
        """Record an event processing error.

        Args:
            event_type: Type of event that failed
        """
        if not self._initialized:
            logger.warning("Metrics not initialized")
            return

        counter = await self._ensure_error_counter(event_type)
        counter.record(1)

    async def record_latency(self, event_type: str, duration: float) -> None:
        """Record event processing duration.

        Args:
            event_type: Type of event
            duration: Processing duration in seconds
        """
        if not self._initialized:
            logger.warning("Metrics not initialized")
            return

        histogram = await self._ensure_latency_histogram(event_type)
        histogram.record(duration)


# Initialize metrics manager
metrics = EventMetrics()


class EventBus(Lifecycle):
    """Event bus for publishing and subscribing to events."""

    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._filters: List[EventFilter] = []

    async def initialize(self) -> None:
        """Initialize event bus."""
        await metrics.initialize()
        logger.info("EventBus initialized")

    async def cleanup(self) -> None:
        """Clean up event bus."""
        self._handlers.clear()
        self._filters.clear()
        logger.info("EventBus cleaned up")

    def add_handler(self, handler: EventHandler) -> None:
        """Add an event handler.

        Args:
            handler: Handler to add
        """
        for event_type in handler.supported_event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
                logger.debug(
                    "Added event handler",
                    extra={
                        "handler": handler.__class__.__name__,
                        "event_type": event_type,
                    },
                )

    def remove_handler(self, handler: EventHandler) -> None:
        """Remove an event handler.

        Args:
            handler: Handler to remove
        """
        for handlers in self._handlers.values():
            if handler in handlers:
                handlers.remove(handler)
                logger.debug(
                    "Removed event handler",
                    extra={"handler": handler.__class__.__name__},
                )

    def add_filter(self, event_filter: EventFilter) -> None:
        """Add an event filter.

        Args:
            event_filter: Filter to add
        """
        if event_filter not in self._filters:
            self._filters.append(event_filter)

    def remove_filter(self, event_filter: EventFilter) -> None:
        """Remove an event filter.

        Args:
            event_filter: Filter to remove
        """
        if event_filter in self._filters:
            self._filters.remove(event_filter)

    async def publish(self, event: Event) -> None:
        """Publish an event.

        Args:
            event: Event to publish
        """
        start_time = datetime.utcnow()

        try:
            # Apply filters
            for event_filter in self._filters:
                if not event_filter.matches(event):
                    logger.debug(
                        "Event filtered",
                        extra={
                            "event_type": event.event_type,
                            "filter": event_filter.__class__.__name__,
                        },
                    )
                    return

            # Get handlers for event type
            handlers = self._handlers.get(event.event_type, [])
            if not handlers:
                logger.warning(
                    "No handlers for event type",
                    extra={"event_type": event.event_type},
                )
                return

            # Process event with each handler
            for handler in handlers:
                try:
                    await handler.handle_event(event)
                    await metrics.record_event(event.event_type)
                except Exception as e:
                    await metrics.record_error(event.event_type)
                    logger.error(
                        "Error handling event",
                        extra={
                            "event_type": event.event_type,
                            "handler": handler.__class__.__name__,
                            "error": str(e),
                        },
                    )

            # Record processing latency
            latency = (datetime.utcnow() - start_time).total_seconds()
            await metrics.record_latency(event.event_type, latency)

            logger.debug(
                "Event published",
                extra={
                    "event_type": event.event_type,
                    "handler_count": len(handlers),
                    "latency": latency,
                },
            )
        except Exception as e:
            await metrics.record_error(event.event_type)
            logger.error(
                "Error publishing event",
                extra={
                    "event_type": event.event_type,
                    "error": str(e),
                },
            )


class EventEmitter:
    """Base class for event emitters."""

    def __init__(self) -> None:
        """Initialize event emitter."""
        self._event_count = 0
        self._error_count = 0

    async def emit(self, event_type: str, **kwargs) -> None:
        """Emit an event.

        Args:
            event_type: Type of event to emit
            **kwargs: Event data
        """
        self._event_count += 1
        await metrics.record_event(event_type)

    async def emit_error(self, error_type: str, error: Exception, **kwargs) -> None:
        """Emit an error event.

        Args:
            error_type: Type of error event
            error: Exception that occurred
            **kwargs: Additional error data
        """
        self._error_count += 1
        await metrics.record_error(error_type)
