"""Event protocols for the Pepperpy framework.

This module provides event-related protocols used throughout the framework.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EventListener(Protocol):
    """Protocol for event listeners."""

    async def on_event(self, event: Any) -> None:
        """Handle event.

        Args:
            event: Event to handle
        """
        ...


@runtime_checkable
class EventHandler(Protocol):
    """Protocol for event handlers."""

    async def handle(self, event: Any) -> None:
        """Handle event.

        Args:
            event: Event to handle
        """
        ...


@runtime_checkable
class EventBus(Protocol):
    """Protocol for event buses."""

    async def publish(self, event: Any) -> None:
        """Publish event.

        Args:
            event: Event to publish
        """
        ...

    async def subscribe(self, event_type: str, listener: EventListener) -> None:
        """Subscribe to event type.

        Args:
            event_type: Event type to subscribe to
            listener: Event listener
        """
        ...

    async def unsubscribe(self, event_type: str, listener: EventListener) -> None:
        """Unsubscribe from event type.

        Args:
            event_type: Event type to unsubscribe from
            listener: Event listener
        """
        ...
