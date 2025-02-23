"""Core event system for the Pepperpy framework.

This module provides the event system functionality for:
- Event bus implementation
- Event handlers and callbacks
- Event prioritization
- Event filtering
- Event middleware
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from enum import Enum, IntEnum
from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.types import ComponentState
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
    metadata: dict[str, Any] = {}


class Event(BaseModel):
    """Base class for all events."""

    event_type: str = Field(description="Type of event")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    source: str = Field(description="Event source")
    data: dict[str, Any] = Field(default_factory=dict, description="Event data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    priority: EventPriority = Field(
        default=EventPriority.NORMAL, description="Event priority"
    )
    event_id: UUID = Field(default_factory=uuid4, description="Event ID")


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
        self._event_types: list[str] = []

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
    def supported_event_types(self) -> list[str]:
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


class EventMiddleware(ABC):
    """Base class for event middleware."""

    @abstractmethod
    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event through middleware.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result
        """
        pass


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

    def __init__(self, allowed_types: list[str]) -> None:
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
            bool: True if event priority meets minimum
        """
        return event.priority >= self._min_priority


class EventMetrics:
    """Event metrics collection."""

    def __init__(self) -> None:
        """Initialize event metrics."""
        self._metrics = MetricsManager.get_instance()
        self._event_counters: dict[str, Counter] = {}
        self._error_counters: dict[str, Counter] = {}
        self._latency_histograms: dict[str, Histogram] = {}

    async def record_event(self, event_type: str) -> None:
        """Record event occurrence.

        Args:
            event_type: Type of event
        """
        counter = await self._ensure_event_counter(event_type)
        counter.increment()

    async def record_error(self, event_type: str) -> None:
        """Record event error.

        Args:
            event_type: Type of event
        """
        counter = await self._ensure_error_counter(event_type)
        counter.increment()

    async def record_latency(self, event_type: str, duration: float) -> None:
        """Record event processing latency.

        Args:
            event_type: Type of event
            duration: Processing duration in seconds
        """
        histogram = await self._ensure_latency_histogram(event_type)
        histogram.observe(duration)

    async def _ensure_event_counter(self, event_type: str) -> Counter:
        """Get or create event counter.

        Args:
            event_type: Type of event

        Returns:
            Event counter
        """
        if event_type not in self._event_counters:
            self._event_counters[event_type] = self._metrics.create_counter(
                f"events_{event_type}_total",
                f"Total number of {event_type} events",
            )
        return self._event_counters[event_type]

    async def _ensure_error_counter(self, event_type: str) -> Counter:
        """Get or create error counter.

        Args:
            event_type: Type of event

        Returns:
            Error counter
        """
        if event_type not in self._error_counters:
            self._error_counters[event_type] = self._metrics.create_counter(
                f"events_{event_type}_errors_total",
                f"Total number of {event_type} event errors",
            )
        return self._error_counters[event_type]

    async def _ensure_latency_histogram(self, event_type: str) -> Histogram:
        """Get or create latency histogram.

        Args:
            event_type: Type of event

        Returns:
            Latency histogram
        """
        if event_type not in self._latency_histograms:
            self._latency_histograms[event_type] = self._metrics.create_histogram(
                f"events_{event_type}_latency_seconds",
                f"Latency of {event_type} event processing",
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )
        return self._latency_histograms[event_type]


class EventBus(Lifecycle):
    """Event bus implementation.

    This class handles event dispatching, filtering, and metrics collection.
    """

    def __init__(self) -> None:
        """Initialize event bus."""
        super().__init__()
        self._handlers: dict[str, set[EventHandler]] = {}
        self._middleware: list[EventMiddleware] = []
        self._filters: list[EventFilter] = []
        self._metrics = EventMetrics()
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize event bus."""
        try:
            self._state = ComponentState.RUNNING
            logger.info("Event bus initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize event bus: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up event bus."""
        try:
            self._handlers.clear()
            self._middleware.clear()
            self._filters.clear()
            self._state = ComponentState.UNREGISTERED
            logger.info("Event bus cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup event bus: {e}")
            raise

    def add_handler(self, handler: EventHandler) -> None:
        """Add event handler.

        Args:
            handler: Event handler to add
        """
        for event_type in handler.supported_event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = set()
            self._handlers[event_type].add(handler)

    def remove_handler(self, handler: EventHandler) -> None:
        """Remove event handler.

        Args:
            handler: Event handler to remove
        """
        for event_type in handler.supported_event_types:
            if event_type in self._handlers:
                self._handlers[event_type].discard(handler)
                if not self._handlers[event_type]:
                    del self._handlers[event_type]

    def add_filter(self, event_filter: EventFilter) -> None:
        """Add event filter.

        Args:
            event_filter: Filter to add
        """
        self._filters.append(event_filter)

    def remove_filter(self, event_filter: EventFilter) -> None:
        """Remove event filter.

        Args:
            event_filter: Filter to remove
        """
        self._filters.remove(event_filter)

    async def publish(self, event: Event) -> None:
        """Publish an event.

        Args:
            event: Event to publish
        """
        if self._state != ComponentState.RUNNING:
            raise RuntimeError("Event bus not running")

        # Apply filters
        for event_filter in self._filters:
            if not event_filter.matches(event):
                return

        # Record metrics
        await self._metrics.record_event(event.event_type)
        start_time = datetime.utcnow()

        try:
            # Process through middleware chain
            async def process_middleware(index: int, event: Event) -> None:
                if index < len(self._middleware):
                    await self._middleware[index].process(
                        event, lambda e: process_middleware(index + 1, e)
                    )
                else:
                    await self._dispatch_to_handlers(event)

            await process_middleware(0, event)

            # Record latency
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._metrics.record_latency(event.event_type, duration)

        except Exception as e:
            await self._metrics.record_error(event.event_type)
            logger.error(f"Error publishing event: {e}")
            raise

    async def _dispatch_to_handlers(self, event: Event) -> None:
        """Dispatch event to registered handlers.

        Args:
            event: Event to dispatch
        """
        handlers = self._handlers.get(event.event_type, set())
        if not handlers:
            logger.debug(f"No handlers for event type: {event.event_type}")
            return

        # Sort handlers by priority
        sorted_handlers = sorted(handlers, key=lambda h: h.priority, reverse=True)

        # Execute handlers
        for handler in sorted_handlers:
            try:
                await handler.handle_event(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                await self._metrics.record_error(event.event_type)


class EventEmitter(Protocol):
    """Protocol for objects that can emit events."""

    async def emit(self, event: Event) -> None:
        """Emit an event.

        Args:
            event: Event to emit
        """
        ...
