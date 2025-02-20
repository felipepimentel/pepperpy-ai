"""Registry event handlers for the Pepperpy framework.

This module provides event handlers specific to registry operations.
"""

from typing import Any, Dict
from uuid import UUID

from pydantic import Field

from pepperpy.events.base import Event, EventHandler, EventType


class RegistryEvent(Event):
    """Event specific to registry operations."""

    # Base Event fields are inherited:
    # id: UUID
    # type: EventType
    # timestamp: datetime
    # data: Dict[str, Any]
    # source_id: Optional[str]
    # priority: EventPriority

    # Registry-specific fields
    registry_id: UUID
    operation: str
    item_type: str
    item_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


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

        if event.type == EventType.PROVIDER_REGISTERED:
            await self.on_item_registered(event)
        elif event.type == EventType.PROVIDER_UNREGISTERED:
            await self.on_item_unregistered(event)
        else:
            await self.on_item_updated(event)
