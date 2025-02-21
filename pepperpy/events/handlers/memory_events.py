"""Memory event handlers and types.

This module provides event handling for memory-related events:
- Memory store/retrieve operations
- Memory updates
- Memory cleanup events
"""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import Field

from pepperpy.events.base import Event, EventHandler, EventPriority, EventType
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


class MemoryEvent(Event):
    """Base class for memory events."""

    memory_id: UUID = Field(..., description="ID of the memory")
    memory_type: str = Field(..., description="Type of memory")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata")

    def __init__(
        self,
        event_type: str,
        priority: EventPriority,
        memory_id: UUID,
        memory_type: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize memory event."""
        super().__init__(event_type=event_type, priority=priority)
        self.memory_id = memory_id
        self.memory_type = memory_type
        self.metadata = metadata


class MemoryStoredEvent(MemoryEvent):
    """Event emitted when a memory is stored."""

    def __init__(
        self,
        memory_id: UUID,
        memory_type: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize memory stored event."""
        super().__init__(
            event_type=str(EventType.MEMORY_STORED),
            priority=EventPriority.NORMAL,
            memory_id=memory_id,
            memory_type=memory_type,
            metadata=metadata,
        )


class MemoryRetrievedEvent(MemoryEvent):
    """Event emitted when a memory is retrieved."""

    def __init__(
        self,
        memory_id: UUID,
        memory_type: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize memory retrieved event."""
        super().__init__(
            event_type=str(EventType.MEMORY_RETRIEVED),
            priority=EventPriority.NORMAL,
            memory_id=memory_id,
            memory_type=memory_type,
            metadata=metadata,
        )


class MemoryUpdatedEvent(MemoryEvent):
    """Event emitted when a memory is updated."""

    def __init__(
        self,
        memory_id: UUID,
        memory_type: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Initialize memory updated event."""
        super().__init__(
            event_type=str(EventType.MEMORY_UPDATED),
            priority=EventPriority.NORMAL,
            memory_id=memory_id,
            memory_type=memory_type,
            metadata=metadata,
        )


class MemoryEventHandler(EventHandler):
    """Handler for memory events."""

    @property
    def supported_event_types(self) -> List[str]:
        """Get supported event types.

        Returns:
            List of supported event types
        """
        return [
            str(EventType.MEMORY_STORED),
            str(EventType.MEMORY_RETRIEVED),
            str(EventType.MEMORY_UPDATED),
        ]

    async def handle_event(self, event: Event) -> None:
        """Handle memory events.

        Args:
            event: Memory event to handle
        """
        if not isinstance(event, MemoryEvent):
            logger.warning(
                "Invalid event type",
                extra={
                    "expected": "MemoryEvent",
                    "received": type(event).__name__,
                },
            )
            return

        # Log event details
        logger.info(
            f"Handling memory event: {event.event_type}",
            extra={
                "memory_id": str(event.memory_id),
                "memory_type": event.memory_type,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
            },
        )

        # Handle specific event types
        if event.event_type == str(EventType.MEMORY_STORED):
            await self._handle_memory_stored(event)  # type: ignore
        elif event.event_type == str(EventType.MEMORY_RETRIEVED):
            await self._handle_memory_retrieved(event)  # type: ignore
        elif event.event_type == str(EventType.MEMORY_UPDATED):
            await self._handle_memory_updated(event)  # type: ignore

    async def _handle_memory_stored(self, event: MemoryStoredEvent) -> None:
        """Handle memory stored event.

        Args:
            event: Memory stored event
        """
        logger.info(
            "Memory stored",
            extra={
                "memory_id": str(event.memory_id),
                "memory_type": event.memory_type,
            },
        )

    async def _handle_memory_retrieved(self, event: MemoryRetrievedEvent) -> None:
        """Handle memory retrieved event.

        Args:
            event: Memory retrieved event
        """
        logger.info(
            "Memory retrieved",
            extra={
                "memory_id": str(event.memory_id),
                "memory_type": event.memory_type,
            },
        )

    async def _handle_memory_updated(self, event: MemoryUpdatedEvent) -> None:
        """Handle memory updated event.

        Args:
            event: Memory updated event
        """
        logger.info(
            "Memory updated",
            extra={
                "memory_id": str(event.memory_id),
                "memory_type": event.memory_type,
            },
        )
