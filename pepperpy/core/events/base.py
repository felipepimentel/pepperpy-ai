"""Base event system for Pepperpy.

This module provides the core event system functionality:
- Event base classes
- Event dispatcher
- Event middleware
- Event context
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState

logger = logging.getLogger(__name__)


class Event(BaseModel):
    """Base class for all events."""

    event_type: str = Field(
        description="Type of event",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp",
    )
    source: str = Field(
        description="Event source",
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event data",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event metadata",
    )


class EventMiddleware(ABC):
    """Base class for event middleware."""

    @abstractmethod
    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event through middleware.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result
        """
        pass


class EventHandler(ABC):
    """Base class for event handlers."""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event.

        Args:
            event: Event to handle
        """
        pass


class EventDispatcher(Lifecycle):
    """Dispatches events to registered handlers."""

    def __init__(self) -> None:
        """Initialize event dispatcher."""
        super().__init__()
        self._handlers: Dict[str, Set[EventHandler]] = {}
        self._middleware: List[EventMiddleware] = []
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize event dispatcher."""
        try:
            self._state = ComponentState.RUNNING
            logger.info("Event dispatcher initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize event dispatcher: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up event dispatcher."""
        try:
            self._handlers.clear()
            self._middleware.clear()
            self._state = ComponentState.UNREGISTERED
            logger.info("Event dispatcher cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup event dispatcher: {e}")
            raise

    def add_middleware(self, middleware: EventMiddleware) -> None:
        """Add middleware to the processing chain.

        Args:
            middleware: Middleware to add
        """
        self._middleware.append(middleware)

    def subscribe(
        self, event_type: str, handler: EventHandler, handler_id: Optional[str] = None
    ) -> None:
        """Subscribe to events.

        Args:
            event_type: Type of events to subscribe to
            handler: Event handler
            handler_id: Optional handler identifier
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = set()
        self._handlers[event_type].add(handler)

    def unsubscribe(
        self, event_type: str, handler: EventHandler, handler_id: Optional[str] = None
    ) -> None:
        """Unsubscribe from events.

        Args:
            event_type: Type of events to unsubscribe from
            handler: Event handler to remove
            handler_id: Optional handler identifier
        """
        if event_type in self._handlers:
            self._handlers[event_type].discard(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]

    async def dispatch(self, event: Event) -> None:
        """Dispatch an event to all registered handlers.

        Args:
            event: Event to dispatch
        """
        if self._state != ComponentState.RUNNING:
            raise RuntimeError("Event dispatcher not running")

        # Process through middleware chain
        async def process_middleware(index: int, event: Event) -> None:
            if index < len(self._middleware):
                await self._middleware[index].process(
                    event, lambda e: process_middleware(index + 1, e)
                )
            else:
                await self._dispatch_to_handlers(event)

        await process_middleware(0, event)

    async def _dispatch_to_handlers(self, event: Event) -> None:
        """Dispatch event to registered handlers.

        Args:
            event: Event to dispatch
        """
        handlers = self._handlers.get(event.event_type, set())
        if not handlers:
            logger.debug(f"No handlers for event type: {event.event_type}")
            return

        tasks = [asyncio.create_task(handler.handle(event)) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)
