"""Event bus for the Pepperpy framework.

This module provides the event bus for handling events.
"""

from typing import Any

from pepperpy.core.events.handlers import EventHandler
from pepperpy.core.events.types import EventType
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)


class EventBus:
    """Event bus for handling events."""

    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: dict[EventType, set[EventHandler]] = {}

    def register_handler(self, event_type: EventType, handler: EventHandler) -> None:
        """Register an event handler.

        Args:
            event_type: Type of event to handle
            handler: Event handler
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = set()
        self._handlers[event_type].add(handler)
        logger.debug(
            "Registered event handler",
            event_type=event_type.name,
            handler=handler.__class__.__name__,
        )

    def unregister_handler(self, event_type: EventType, handler: EventHandler) -> None:
        """Unregister an event handler.

        Args:
            event_type: Type of event
            handler: Event handler
        """
        if event_type in self._handlers:
            self._handlers[event_type].discard(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]
            logger.debug(
                "Unregistered event handler",
                event_type=event_type.name,
                handler=handler.__class__.__name__,
            )

    async def emit(self, event_type: EventType, **data: Any) -> None:
        """Emit an event.

        Args:
            event_type: Type of event
            **data: Event data
        """
        if event_type in self._handlers:
            logger.debug(
                "Emitting event",
                event_type=event_type.name,
                handlers=len(self._handlers[event_type]),
            )
            for handler in self._handlers[event_type]:
                try:
                    await handler.handle_event(event_type, **data)
                except Exception as e:
                    logger.error(
                        "Event handler failed",
                        event_type=event_type.name,
                        handler=handler.__class__.__name__,
                        error=str(e),
                    )


__all__ = ["EventBus"]
