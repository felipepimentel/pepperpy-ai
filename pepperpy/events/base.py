"""Base event module for the Pepperpy framework.

This module provides core event functionality including:
- Event types and definitions
- Event bus implementation
- Event handlers and listeners
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pepperpy.core.errors import ValidationError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.models import BaseModel, ConfigDict, Field
from pepperpy.core.types import ComponentState
from pepperpy.events.protocols import EventHandler, EventListener


class EventType(str, Enum):
    """Event types."""

    SYSTEM = "SYSTEM"
    COMPONENT = "COMPONENT"
    AGENT = "AGENT"
    WORKFLOW = "WORKFLOW"
    RESOURCE = "RESOURCE"
    CAPABILITY = "CAPABILITY"
    PROVIDER = "PROVIDER"
    CUSTOM = "CUSTOM"


class Event(BaseModel):
    """Event model.

    Attributes:
        id: Event ID
        type: Event type
        name: Event name
        data: Event data
        timestamp: Event timestamp
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    id: UUID = Field(default_factory=uuid4, description="Event ID")
    type: EventType = Field(description="Event type")
    name: str = Field(description="Event name")
    data: dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp",
    )


class EventManager(Lifecycle):
    """Event manager."""

    def __init__(self) -> None:
        """Initialize event manager."""
        self._state = ComponentState.CREATED
        self._handlers: dict[str, list[EventHandler]] = {}
        self._listeners: dict[str, list[EventListener]] = {}
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None

    async def initialize(self) -> None:
        """Initialize manager."""
        try:
            self._state = ComponentState.INITIALIZING
            self._task = asyncio.create_task(self._process_events())
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize manager: {e}")

    async def cleanup(self) -> None:
        """Clean up manager."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                await self._task
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up manager: {e}")

    def add_handler(self, event_type: str, handler: EventHandler) -> None:
        """Add event handler.

        Args:
            event_type: Event type to handle
            handler: Event handler

        Raises:
            ValidationError: If handler already exists
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler in self._handlers[event_type]:
            raise ValidationError(
                f"Handler already exists for event type: {event_type}"
            )
        self._handlers[event_type].append(handler)

    def remove_handler(self, event_type: str, handler: EventHandler) -> None:
        """Remove event handler.

        Args:
            event_type: Event type to handle
            handler: Event handler

        Raises:
            ValidationError: If handler not found
        """
        if event_type not in self._handlers:
            raise ValidationError(f"No handlers found for event type: {event_type}")
        if handler not in self._handlers[event_type]:
            raise ValidationError(f"Handler not found for event type: {event_type}")
        self._handlers[event_type].remove(handler)

    def add_listener(self, event_type: str, listener: EventListener) -> None:
        """Add event listener.

        Args:
            event_type: Event type to listen for
            listener: Event listener

        Raises:
            ValidationError: If listener already exists
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if listener in self._listeners[event_type]:
            raise ValidationError(
                f"Listener already exists for event type: {event_type}"
            )
        self._listeners[event_type].append(listener)

    def remove_listener(self, event_type: str, listener: EventListener) -> None:
        """Remove event listener.

        Args:
            event_type: Event type to listen for
            listener: Event listener

        Raises:
            ValidationError: If listener not found
        """
        if event_type not in self._listeners:
            raise ValidationError(f"No listeners found for event type: {event_type}")
        if listener not in self._listeners[event_type]:
            raise ValidationError(f"Listener not found for event type: {event_type}")
        self._listeners[event_type].remove(listener)

    async def publish(self, event: Event) -> None:
        """Publish event.

        Args:
            event: Event to publish
        """
        await self._queue.put(event)

    async def _process_events(self) -> None:
        """Process events from queue."""
        while True:
            try:
                event = await self._queue.get()
                await self._handle_event(event)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Failed to process event: {e}", exc_info=True)

    async def _handle_event(self, event: Event) -> None:
        """Handle event.

        Args:
            event: Event to handle
        """
        event_type = event.type
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    await handler.handle(event)
                except Exception as e:
                    logging.error(
                        f"Handler failed for event {event.id}: {e}",
                        exc_info=True,
                    )
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                try:
                    await listener.on_event(event)
                except Exception as e:
                    logging.error(
                        f"Listener failed for event {event.id}: {e}",
                        exc_info=True,
                    )


# Export public API
__all__ = [
    "Event",
    "EventManager",
    "EventType",
]
