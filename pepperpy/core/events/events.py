"""Core events module.

This module provides event handling functionality including:
- Event types
- Event bus
- Event handlers
"""

from collections.abc import Callable, Coroutine
from enum import Enum, auto
from typing import Any


class EventType(Enum):
    """Types of system events."""

    LIFECYCLE = auto()
    SECURITY = auto()
    METRICS = auto()
    ERROR = auto()
    STATE = auto()
    RESOURCE = auto()
    PROVIDER = auto()
    EXTENSION = auto()


EventHandler = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


class EventBus:
    """Event bus for system events."""

    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: dict[EventType, list[EventHandler]] = {}

    async def emit(
        self,
        event_type: EventType,
        event_name: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Emit event to registered handlers.

        Args:
            event_type: Type of event
            event_name: Name of event
            data: Optional event data
        """
        if event_type not in self._handlers:
            return

        event_data = data or {}
        for handler in self._handlers[event_type]:
            await handler(event_name, event_data)

    def on(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """Register event handler.

        Args:
            event_type: Type of event to handle
            handler: Event handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def off(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """Unregister event handler.

        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
