"""Registry event handlers for the Pepperpy framework.

This module provides event handlers for registry operations.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pepperpy.core.events.handlers import EventHandler
from pepperpy.core.events.types import EventType
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)


@dataclass
class RegistryEvent:
    """Event data for registry operations."""

    event_type: EventType
    registry_id: UUID
    operation: str
    item_type: str
    item_key: str | None = None
    item_version: str | None = None
    metadata: dict[str, Any] | None = None


class RegistryEventHandler(EventHandler):
    """Event handler for registry operations."""

    async def handle_event(self, event_type: EventType, **data: Any) -> None:
        """Handle a registry event.

        Args:
            event_type: Type of event
            **data: Event data
        """
        if event_type in {
            EventType.PROVIDER_REGISTERED,
            EventType.PROVIDER_UNREGISTERED,
            EventType.PROVIDER_UPDATED,
        }:
            await self._handle_provider_event(event_type, **data)

    async def _handle_provider_event(self, event_type: EventType, **data: Any) -> None:
        """Handle a provider event.

        Args:
            event_type: Type of event
            **data: Event data
        """
        event = RegistryEvent(
            event_type=event_type,
            registry_id=data["registry_id"],
            operation=data["operation"],
            item_type=data["item_type"],
            item_key=data.get("item_key"),
            item_version=data.get("item_version"),
            metadata=data.get("metadata"),
        )
        logger.info(
            "Registry event",
            event_type=event_type.name,
            operation=event.operation,
            item_type=event.item_type,
            item_key=event.item_key,
            item_version=event.item_version,
        )


__all__ = ["RegistryEvent", "RegistryEventHandler"]
