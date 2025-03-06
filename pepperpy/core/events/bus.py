"""Event bus for the PepperPy framework.

This module provides an event bus implementation for the framework,
allowing components to subscribe to and publish events.
"""

from typing import Any, Callable, Dict, Optional, Set, TypeVar

from pepperpy.core.events.types import EventType

T = TypeVar("T")


class EventBus:
    """Event bus for the PepperPy framework.

    This class provides methods to subscribe to, unsubscribe from, and publish events.
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[EventType, Set[Callable]] = {}

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to an event.

        Args:
            event_type: The type of event to subscribe to.
            callback: The callback function to be called when the event is published.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Unsubscribe from an event.

        Args:
            event_type: The type of event to unsubscribe from.
            callback: The callback function to be removed.
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    async def publish(self, event_type: EventType, data: Optional[Any] = None) -> None:
        """Publish an event.

        Args:
            event_type: The type of event to publish.
            data: Optional data to be passed to the subscribers.
        """
        if event_type not in self._subscribers:
            return

        # Make a copy of the subscribers to avoid issues if the set changes during iteration
        subscribers = list(self._subscribers[event_type])
        for callback in subscribers:
            if data is not None:
                await callback(data)
            else:
                await callback()

    def clear(self) -> None:
        """Clear all subscribers."""
        self._subscribers.clear()


# Singleton instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the singleton event bus instance.

    Returns:
        The event bus instance.
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
