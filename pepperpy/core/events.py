"""
Core events module defining the event system functionality.

This module provides the base classes and interfaces for the event-driven
architecture used throughout PepperPy.
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Set
from uuid import UUID

from ..types import Event


class EventListener(ABC):
    """Base class for event listeners."""

    def __init__(self, name: str):
        self.name = name
        self.id = UUID()

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Handle an incoming event."""
        pass

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EventListener):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class EventFilter(ABC):
    """Base class for event filters."""

    @abstractmethod
    def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        pass


class EventTypeFilter(EventFilter):
    """Filter events by type."""

    def __init__(self, event_type: str):
        self.event_type = event_type

    def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        return event.type == self.event_type


class EventSourceFilter(EventFilter):
    """Filter events by source."""

    def __init__(self, source: str):
        self.source = source

    def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        return event.source == self.source


class EventBus:
    """Central event bus for dispatching events to listeners."""

    def __init__(self):
        self._listeners: Dict[str, Set[EventListener]] = {}
        self._filters: Dict[UUID, List[EventFilter]] = {}
        self._middleware: List[Callable[[Event], Event]] = []

    def add_listener(
        self,
        event_type: str,
        listener: EventListener,
        filters: Optional[List[EventFilter]] = None,
    ) -> None:
        """Add a listener for events of a specific type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = set()

        self._listeners[event_type].add(listener)

        if filters:
            self._filters[listener.id] = filters

    def remove_listener(self, event_type: str, listener: EventListener) -> None:
        """Remove a listener for events of a specific type."""
        if event_type in self._listeners:
            self._listeners[event_type].discard(listener)
            if listener.id in self._filters:
                del self._filters[listener.id]

    def add_middleware(self, middleware: Callable[[Event], Event]) -> None:
        """Add middleware to process events before dispatch."""
        self._middleware.append(middleware)

    async def publish(self, event: Event) -> None:
        """Publish an event to all registered listeners."""
        # Apply middleware
        for middleware in self._middleware:
            event = middleware(event)

        # Get listeners for this event type
        listeners = self._listeners.get(event.type, set())

        # Dispatch to matching listeners
        for listener in listeners:
            # Check filters
            if listener.id in self._filters:
                filters = self._filters[listener.id]
                if not all(f.matches(event) for f in filters):
                    continue

            await listener.handle_event(event)

    def clear(self) -> None:
        """Clear all listeners and filters."""
        self._listeners.clear()
        self._filters.clear()
        self._middleware.clear()


class AsyncEventListener(EventListener):
    """Base class for asynchronous event listeners."""

    def __init__(self, name: str, callback: Callable[[Event], None]):
        super().__init__(name)
        self._callback = callback

    async def handle_event(self, event: Event) -> None:
        """Handle an incoming event by calling the callback."""
        self._callback(event)


def create_event_bus() -> EventBus:
    """Create and configure a new event bus instance."""
    return EventBus()


# Export all types
__all__ = [
    "Event",
    "EventListener",
    "AsyncEventListener",
    "EventFilter",
    "EventTypeFilter",
    "EventSourceFilter",
    "EventBus",
    "create_event_bus",
]
