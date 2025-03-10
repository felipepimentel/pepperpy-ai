"""Core functionality for event handling in PepperPy.

This module provides the core functionality for event handling in PepperPy,
including event definition, event emitting, and event handling.
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar, Union, cast, Awaitable

from pepperpy.interfaces import AsyncHandler, Handler
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for event data
T = TypeVar("T")
EventCallback = Callable[["Event[Any]"], None]
AsyncEventCallback = Callable[["Event[Any]"], Awaitable[None]]


@dataclass
class Event(Generic[T]):
    """Base class for events.

    An event represents something that happened in the system. It has a type, data,
    and metadata.
    """

    event_type: str
    data: T
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        """Get a string representation of the event.

        Returns:
            A string representation of the event
        """
        return f"{self.event_type}: {self.data}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            The event as a dictionary
        """
        return {
            "event_type": self.event_type,
            "data": self.data,
            "metadata": self.metadata,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event[Any]":
        """Create an event from a dictionary.

        Args:
            data: The dictionary to create the event from

        Returns:
            The created event
        """
        return cls(
            event_type=data["event_type"],
            data=data["data"],
            metadata=data.get("metadata", {}),
            event_id=data.get("event_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", time.time()),
        )


class EventPriority(Enum):
    """Priority levels for event handlers.

    Event handlers with higher priority are executed before those with lower priority.
    """

    HIGHEST = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    LOWEST = 0


@dataclass
class EventHandler(Generic[T]):
    """Event handler.

    An event handler is responsible for handling events of a specific type.
    """

    event_type: str
    callback: Callable[[Event[T]], None]
    priority: EventPriority = EventPriority.NORMAL
    handler_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def handle(self, event: Event[T]) -> None:
        """Handle an event.

        Args:
            event: The event to handle
        """
        try:
            self.callback(event)
        except Exception as e:
            logger.error(f"Error handling event {event.event_type}: {e}")
            logger.debug("Exception details:", exc_info=True)


@dataclass
class AsyncEventHandler(Generic[T]):
    """Asynchronous event handler.

    An asynchronous event handler is responsible for handling events of a specific type
    asynchronously.
    """

    event_type: str
    callback: Callable[[Event[T]], Awaitable[None]]
    priority: EventPriority = EventPriority.NORMAL
    handler_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    async def handle(self, event: Event[T]) -> None:
        """Handle an event asynchronously.

        Args:
            event: The event to handle
        """
        try:
            await self.callback(event)
        except Exception as e:
            logger.error(f"Error handling event {event.event_type}: {e}")
            logger.debug("Exception details:", exc_info=True)


class EventBus:
    """Event bus for emitting and handling events.

    The event bus is responsible for routing events to their handlers.
    """

    def __init__(self):
        """Initialize an event bus."""
        self.handlers: Dict[str, List[EventHandler[Any]]] = {}
        self.async_handlers: Dict[str, List[AsyncEventHandler[Any]]] = {}

    def emit(self, event: Event[Any]) -> None:
        """Emit an event.

        Args:
            event: The event to emit
        """
        # Log the event
        logger.debug(f"Emitting event {event.event_type}: {event.data}")

        # Get handlers for the event type
        handlers = self.handlers.get(event.event_type, [])

        # Sort handlers by priority (highest first)
        sorted_handlers = sorted(handlers, key=lambda h: h.priority.value, reverse=True)

        # Handle the event
        for handler in sorted_handlers:
            try:
                handler.handle(event)
            except Exception as e:
                logger.error(f"Error handling event {event.event_type}: {e}")
                logger.debug("Exception details:", exc_info=True)

    async def emit_async(self, event: Event[Any]) -> None:
        """Emit an event asynchronously.

        Args:
            event: The event to emit
        """
        # Log the event
        logger.debug(f"Emitting async event {event.event_type}: {event.data}")

        # Get synchronous handlers for the event type
        handlers = self.handlers.get(event.event_type, [])

        # Get asynchronous handlers for the event type
        async_handlers = self.async_handlers.get(event.event_type, [])

        # Sort handlers by priority (highest first)
        sorted_handlers = sorted(handlers, key=lambda h: h.priority.value, reverse=True)
        sorted_async_handlers = sorted(
            async_handlers, key=lambda h: h.priority.value, reverse=True
        )

        # Handle the event with synchronous handlers
        for handler in sorted_handlers:
            try:
                handler.handle(event)
            except Exception as e:
                logger.error(f"Error handling event {event.event_type}: {e}")
                logger.debug("Exception details:", exc_info=True)

        # Handle the event with asynchronous handlers
        for handler in sorted_async_handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(f"Error handling async event {event.event_type}: {e}")
                logger.debug("Exception details:", exc_info=True)

    def on(
        self,
        event_type: str,
        callback: EventCallback,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> EventHandler[Any]:
        """Register an event handler.

        Args:
            event_type: The type of events to handle
            callback: The callback to call when an event is emitted
            priority: The priority of the handler

        Returns:
            The registered event handler
        """
        # Create a handler
        handler = EventHandler(
            event_type=event_type,
            callback=callback,
            priority=priority,
        )

        # Register the handler
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)

        # Log the registration
        logger.debug(f"Registered handler {handler.handler_id} for event {event_type}")

        return handler

    def on_async(
        self,
        event_type: str,
        callback: AsyncEventCallback,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> AsyncEventHandler[Any]:
        """Register an asynchronous event handler.

        Args:
            event_type: The type of events to handle
            callback: The callback to call when an event is emitted
            priority: The priority of the handler

        Returns:
            The registered event handler
        """
        # Create a handler
        handler = AsyncEventHandler(
            event_type=event_type,
            callback=callback,
            priority=priority,
        )

        # Register the handler
        if event_type not in self.async_handlers:
            self.async_handlers[event_type] = []

        self.async_handlers[event_type].append(handler)

        # Log the registration
        logger.debug(
            f"Registered async handler {handler.handler_id} for event {event_type}"
        )

        return handler

    def off(self, handler: Union[EventHandler[Any], AsyncEventHandler[Any]]) -> None:
        """Unregister an event handler.

        Args:
            handler: The handler to unregister
        """
        # Check if the handler is an EventHandler
        if isinstance(handler, EventHandler):
            # Get handlers for the event type
            handlers = self.handlers.get(handler.event_type, [])

            # Remove the handler
            self.handlers[handler.event_type] = [
                h for h in handlers if h.handler_id != handler.handler_id
            ]

            # Log the unregistration
            logger.debug(
                f"Unregistered handler {handler.handler_id} for event {handler.event_type}"
            )

        # Check if the handler is an AsyncEventHandler
        elif isinstance(handler, AsyncEventHandler):
            # Get handlers for the event type
            handlers = self.async_handlers.get(handler.event_type, [])

            # Remove the handler
            self.async_handlers[handler.event_type] = [
                h for h in handlers if h.handler_id != handler.handler_id
            ]

            # Log the unregistration
            logger.debug(
                f"Unregistered async handler {handler.handler_id} for event {handler.event_type}"
            )

    def off_all(self, event_type: Optional[str] = None) -> None:
        """Unregister all event handlers.

        Args:
            event_type: The type of events to unregister handlers for, or None to unregister all handlers
        """
        if event_type is None:
            # Unregister all handlers
            self.handlers = {}
            self.async_handlers = {}

            # Log the unregistration
            logger.debug("Unregistered all handlers")
        else:
            # Unregister handlers for the event type
            self.handlers.pop(event_type, None)
            self.async_handlers.pop(event_type, None)

            # Log the unregistration
            logger.debug(f"Unregistered all handlers for event {event_type}")


class EventHandlerAdapter(Handler[Event[Any]]):
    """Adapter for event handlers.

    This adapter allows event handlers to be used as handlers.
    """

    def __init__(
        self,
        event_bus: EventBus,
        event_type: str,
        priority: EventPriority = EventPriority.NORMAL,
    ):
        """Initialize an event handler adapter.

        Args:
            event_bus: The event bus to register the handler with
            event_type: The type of events to handle
            priority: The priority of the handler
        """
        self.event_bus = event_bus
        self.event_type = event_type
        self.priority = priority
        self.handler: Optional[EventHandler[Any]] = None

    def handle(self, event: Event[Any]) -> None:
        """Handle an event.

        Args:
            event: The event to handle
        """
        # Register the handler if it's not registered
        if self.handler is None:
            self.handler = self.event_bus.on(
                event_type=self.event_type,
                callback=lambda e: None,  # Placeholder callback
                priority=self.priority,
            )

        # Override the handler's callback
        self.handler.callback = lambda e: self.event_bus.emit(event)


class AsyncEventHandlerAdapter(AsyncHandler[Event[Any]]):
    """Adapter for asynchronous event handlers.

    This adapter allows asynchronous event handlers to be used as handlers.
    """

    def __init__(
        self,
        event_bus: EventBus,
        event_type: str,
        priority: EventPriority = EventPriority.NORMAL,
    ):
        """Initialize an asynchronous event handler adapter.

        Args:
            event_bus: The event bus to register the handler with
            event_type: The type of events to handle
            priority: The priority of the handler
        """
        self.event_bus = event_bus
        self.event_type = event_type
        self.priority = priority
        self.handler: Optional[AsyncEventHandler[Any]] = None

    async def ahandle(self, event: Event[Any]) -> None:
        """Handle an event asynchronously.

        Args:
            event: The event to handle
        """
        # Register the handler if it's not registered
        if self.handler is None:
            self.handler = self.event_bus.on_async(
                event_type=self.event_type,
                callback=lambda e: asyncio.sleep(0),  # Placeholder callback
                priority=self.priority,
            )

        # Override the handler's callback
        self.handler.callback = lambda e: self.event_bus.emit_async(event)


# Global event bus
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus.

    Returns:
        The global event bus
    """
    return _event_bus


def emit(event: Event[Any]) -> None:
    """Emit an event on the global event bus.

    Args:
        event: The event to emit
    """
    _event_bus.emit(event)


async def emit_async(event: Event[Any]) -> None:
    """Emit an event asynchronously on the global event bus.

    Args:
        event: The event to emit
    """
    await _event_bus.emit_async(event)


def on(
    event_type: str,
    callback: EventCallback,
    priority: EventPriority = EventPriority.NORMAL,
) -> EventHandler[Any]:
    """Register an event handler on the global event bus.

    Args:
        event_type: The type of events to handle
        callback: The callback to call when an event is emitted
        priority: The priority of the handler

    Returns:
        The registered event handler
    """
    return _event_bus.on(event_type, callback, priority)


def on_async(
    event_type: str,
    callback: AsyncEventCallback,
    priority: EventPriority = EventPriority.NORMAL,
) -> AsyncEventHandler[Any]:
    """Register an asynchronous event handler on the global event bus.

    Args:
        event_type: The type of events to handle
        callback: The callback to call when an event is emitted
        priority: The priority of the handler

    Returns:
        The registered event handler
    """
    return _event_bus.on_async(event_type, callback, priority)


def off(handler: Union[EventHandler[Any], AsyncEventHandler[Any]]) -> None:
    """Unregister an event handler from the global event bus.

    Args:
        handler: The handler to unregister
    """
    _event_bus.off(handler)


def off_all(event_type: Optional[str] = None) -> None:
    """Unregister all event handlers from the global event bus.

    Args:
        event_type: The type of events to unregister handlers for, or None to unregister all handlers
    """
    _event_bus.off_all(event_type)
