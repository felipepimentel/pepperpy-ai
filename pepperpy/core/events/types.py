"""Event-related type definitions for the Pepperpy framework."""

from __future__ import annotations

from enum import Enum, auto
from typing import Any, Protocol, TypeVar, runtime_checkable
from uuid import UUID, uuid4

from pepperpy.core.models import BaseModel, ConfigDict

# Type variables for events
T_Event = TypeVar("T_Event", bound="Event")
T_Handler = TypeVar("T_Handler", bound="EventHandler")


class EventType(Enum):
    """Types of events that can be emitted."""

    SYSTEM = auto()
    AGENT = auto()
    WORKFLOW = auto()
    RESOURCE = auto()
    SECURITY = auto()
    MONITORING = auto()
    USER = auto()


class Event(BaseModel):
    """Base event class.

    Attributes:
        id: Unique identifier for the event
        type: Type of event
        data: Event data
        metadata: Additional metadata
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    id: UUID
    type: EventType
    data: dict[str, Any] = {}
    metadata: dict[str, Any] = {}

    def __init__(self, **data: Any) -> None:
        if "id" not in data:
            data["id"] = uuid4()
        super().__init__(**data)


@runtime_checkable
class EventHandler(Protocol[T_Event]):
    """Protocol for event handlers."""

    async def handle(self, event: T_Event) -> None:
        """Handle an event.

        Args:
            event: The event to handle
        """
        ...


@runtime_checkable
class EventBus(Protocol):
    """Protocol for event buses."""

    async def emit(self, event: Event) -> None:
        """Emit an event.

        Args:
            event: The event to emit
        """
        ...

    async def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: The type of events to subscribe to
            handler: The handler to call when events are emitted
        """
        ...

    async def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe from events of a specific type.

        Args:
            event_type: The type of events to unsubscribe from
            handler: The handler to remove
        """
        ...


__all__ = [
    # Type variables
    "T_Event",
    "T_Handler",
    # Enums
    "EventType",
    # Models
    "Event",
    # Protocols
    "EventHandler",
    "EventBus",
]
