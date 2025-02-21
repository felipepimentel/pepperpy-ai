"""Registry event handlers for the Pepperpy framework.

This module provides event handlers specific to registry operations.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from pepperpy.events.base import Event, EventHandler, EventType


class RegistryEvent(Event):
    """Event specific to registry operations."""

    def __init__(
        self,
        event_type: EventType,
        registry_id: UUID,
        operation: str,
        item_type: str,
        item_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize registry event.

        Args:
            event_type: Type of event
            registry_id: Registry identifier
            operation: Operation being performed
            item_type: Type of item being operated on
            item_id: ID of item being operated on
            metadata: Optional event metadata
        """
        super().__init__(event_type=str(event_type), metadata=metadata or {})
        self.registry_id = registry_id
        self.operation = operation
        self.item_type = item_type
        self.item_id = item_id


class RegistryEventHandler(EventHandler):
    """Base class for registry event handlers."""

    async def on_item_registered(self, event: RegistryEvent) -> None:
        """Handle item registration event."""
        pass

    async def on_item_unregistered(self, event: RegistryEvent) -> None:
        """Handle item unregistration event."""
        pass

    async def on_item_updated(self, event: RegistryEvent) -> None:
        """Handle item update event."""
        pass

    async def handle_event(self, event: Event) -> None:
        """Route events to specific handlers.

        Args:
            event: The event to handle

        Raises:
            ValueError: If event is not a RegistryEvent
        """
        if not isinstance(event, RegistryEvent):
            raise ValueError("Expected RegistryEvent")

        if event.event_type == str(EventType.PROVIDER_REGISTERED):
            await self.on_item_registered(event)
        elif event.event_type == str(EventType.PROVIDER_UNREGISTERED):
            await self.on_item_unregistered(event)
        else:
            await self.on_item_updated(event)
