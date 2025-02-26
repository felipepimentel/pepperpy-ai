"""Core event system for the Pepperpy framework.

This module provides a unified event system with:
- Strongly typed events and handlers
- Consistent event bus interface
- Standardized event types
- Observability integration
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar
from uuid import UUID, uuid4

from pepperpy.core.metrics import MetricsManager
from pepperpy.core.observability import ObservabilityManager
from pepperpy.core.models import BaseModel, ConfigDict
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.types import ComponentState

# Type variables
T_Event = TypeVar("T_Event", bound="Event")
T_Data = TypeVar("T_Data")


class Event(BaseModel, Generic[T_Data]):
    """Base event class.
    
    Attributes:
        id: Unique identifier for the event
        type: Type of event
        data: Event data
        metadata: Additional metadata
        timestamp: Event creation timestamp
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    id: UUID = UUID(int=0)
    type: str
    data: T_Data
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()

    def __init__(self, **data: Any) -> None:
        """Initialize event.
        
        Args:
            **data: Event data
        """
        if "id" not in data:
            data["id"] = uuid4()
        if "timestamp" not in data:
            data["timestamp"] = datetime.now()
        super().__init__(**data)


class EventHandler(Protocol[T_Event]):
    """Protocol for event handlers."""

    async def handle(self, event: T_Event) -> None:
        """Handle an event.
        
        Args:
            event: Event to handle
        """
        ...


class EventListener(Protocol[T_Event]):
    """Protocol for event listeners."""

    async def on_event(self, event: T_Event) -> None:
        """Handle an event.
        
        Args:
            event: Event to handle
        """
        ...


class EventBus(Lifecycle):
    """Unified event bus implementation.
    
    Features:
    - Type-safe event handling
    - Async event processing
    - Metrics and monitoring
    - Error handling and recovery
    """

    def __init__(self) -> None:
        """Initialize event bus."""
        self._state = ComponentState.CREATED
        self._handlers: Dict[str, List[EventHandler[Any]]] = {}
        self._listeners: Dict[str, List[EventListener[Any]]] = {}
        self._queue: asyncio.Queue[Event[Any]] = asyncio.Queue()
        self._task: Optional[asyncio.Task[None]] = None
        self._metrics = MetricsManager.get_instance()
        self._observability = ObservabilityManager.get_instance()
        self._logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize event bus."""
        try:
            self._state = ComponentState.INITIALIZING
            self._task = asyncio.create_task(self._process_events())
            self._state = ComponentState.READY
            self._logger.info("Event bus initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            self._logger.error(f"Failed to initialize event bus: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up event bus."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                await self._task
            self._state = ComponentState.CLEANED
            self._logger.info("Event bus cleaned up")
        except Exception as e:
            self._state = ComponentState.ERROR
            self._logger.error(f"Failed to clean up event bus: {e}")
            raise

    def subscribe_handler(
        self,
        event_type: str,
        handler: EventHandler[T_Event],
    ) -> None:
        """Subscribe an event handler.
        
        Args:
            event_type: Type of events to handle
            handler: Event handler
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            self._logger.debug(f"Handler subscribed to {event_type}")

    def unsubscribe_handler(
        self,
        event_type: str,
        handler: EventHandler[T_Event],
    ) -> None:
        """Unsubscribe an event handler.
        
        Args:
            event_type: Type of events to handle
            handler: Event handler
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            self._logger.debug(f"Handler unsubscribed from {event_type}")

    def subscribe_listener(
        self,
        event_type: str,
        listener: EventListener[T_Event],
    ) -> None:
        """Subscribe an event listener.
        
        Args:
            event_type: Type of events to listen for
            listener: Event listener
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if listener not in self._listeners[event_type]:
            self._listeners[event_type].append(listener)
            self._logger.debug(f"Listener subscribed to {event_type}")

    def unsubscribe_listener(
        self,
        event_type: str,
        listener: EventListener[T_Event],
    ) -> None:
        """Unsubscribe an event listener.
        
        Args:
            event_type: Type of events to listen for
            listener: Event listener
        """
        if event_type in self._listeners and listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)
            self._logger.debug(f"Listener unsubscribed from {event_type}")

    async def publish(self, event: Event[T_Data]) -> None:
        """Publish an event.
        
        Args:
            event: Event to publish
        """
        await self._queue.put(event)
        self._metrics.counter(
            "events_published",
            1,
            event_type=event.type,
        )
        self._logger.debug(f"Event published: {event.id} ({event.type})")

    async def _process_events(self) -> None:
        """Process events from queue."""
        while True:
            try:
                event = await self._queue.get()
                start_time = datetime.now()
                
                await self._handle_event(event)
                
                duration = (datetime.now() - start_time).total_seconds()
                self._metrics.histogram(
                    "event_processing_duration",
                    duration,
                    event_type=event.type,
                )
                
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                self._logger.error(
                    f"Failed to process event: {e}",
                    exc_info=True,
                    extra={"event_type": getattr(event, "type", None)},
                )
                self._metrics.counter(
                    "event_processing_errors",
                    1,
                    event_type=getattr(event, "type", "unknown"),
                    error_type=type(e).__name__,
                )

    async def _handle_event(self, event: Event[Any]) -> None:
        """Handle an event.
        
        Args:
            event: Event to handle
        """
        event_type = event.type
        handlers = self._handlers.get(event_type, [])
        listeners = self._listeners.get(event_type, [])
        
        # Track number of handlers/listeners
        self._metrics.gauge(
            "event_handlers",
            len(handlers),
            event_type=event_type,
        )
        self._metrics.gauge(
            "event_listeners",
            len(listeners),
            event_type=event_type,
        )
        
        # Process handlers
        for handler in handlers:
            try:
                await handler.handle(event)
                self._metrics.counter(
                    "event_handler_success",
                    1,
                    event_type=event_type,
                    handler=type(handler).__name__,
                )
            except Exception as e:
                self._logger.error(
                    f"Handler failed for event {event.id}: {e}",
                    exc_info=True,
                    extra={
                        "event_type": event_type,
                        "handler": type(handler).__name__,
                    },
                )
                self._metrics.counter(
                    "event_handler_errors",
                    1,
                    event_type=event_type,
                    handler=type(handler).__name__,
                    error_type=type(e).__name__,
                )
        
        # Process listeners
        for listener in listeners:
            try:
                await listener.on_event(event)
                self._metrics.counter(
                    "event_listener_success",
                    1,
                    event_type=event_type,
                    listener=type(listener).__name__,
                )
            except Exception as e:
                self._logger.error(
                    f"Listener failed for event {event.id}: {e}",
                    exc_info=True,
                    extra={
                        "event_type": event_type,
                        "listener": type(listener).__name__,
                    },
                )
                self._metrics.counter(
                    "event_listener_errors",
                    1,
                    event_type=event_type,
                    listener=type(listener).__name__,
                    error_type=type(e).__name__,
                ) 