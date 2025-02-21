"""Event dispatcher for asynchronous event handling.

This module provides the event dispatcher functionality for:
- Asynchronous event dispatching
- Event handler subscription
- Middleware processing chain
"""

from typing import Dict, List, Set

from pepperpy.core.base import Lifecycle
from pepperpy.events.base import Event, EventHandler
from pepperpy.events.middleware import EventMiddleware
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


class EventDispatcher(Lifecycle):
    """Asynchronous event dispatcher with middleware support."""

    def __init__(self) -> None:
        """Initialize event dispatcher."""
        self._handlers: Dict[str, Set[EventHandler]] = {}
        self._middleware: List[EventMiddleware] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize dispatcher and middleware."""
        if self._initialized:
            return

        # Initialize all middleware
        for middleware in self._middleware:
            if hasattr(middleware, "initialize"):
                await middleware.initialize()

        self._initialized = True
        logger.info("Event dispatcher initialized")

    async def cleanup(self) -> None:
        """Clean up dispatcher resources."""
        self._handlers.clear()
        self._middleware.clear()
        self._initialized = False
        logger.info("Event dispatcher cleaned up")

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Handler to subscribe
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = set()
        self._handlers[event_type].add(handler)
        logger.debug(
            "Handler subscribed",
            extra={
                "event_type": event_type,
                "handler": handler.__class__.__name__,
            },
        )

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to unsubscribe
        """
        if event_type in self._handlers:
            self._handlers[event_type].discard(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]
            logger.debug(
                "Handler unsubscribed",
                extra={
                    "event_type": event_type,
                    "handler": handler.__class__.__name__,
                },
            )

    def add_middleware(self, middleware: EventMiddleware) -> None:
        """Add middleware to the processing chain.

        Args:
            middleware: Middleware to add
        """
        if middleware not in self._middleware:
            self._middleware.append(middleware)
            logger.debug(
                "Middleware added",
                extra={"middleware": middleware.__class__.__name__},
            )

    def remove_middleware(self, middleware: EventMiddleware) -> None:
        """Remove middleware from the processing chain.

        Args:
            middleware: Middleware to remove
        """
        if middleware in self._middleware:
            self._middleware.remove(middleware)
            logger.debug(
                "Middleware removed",
                extra={"middleware": middleware.__class__.__name__},
            )

    async def dispatch(self, event: Event) -> None:
        """Dispatch an event through the middleware chain to handlers.

        Args:
            event: Event to dispatch
        """
        if not self._initialized:
            logger.warning("Dispatcher not initialized")
            return

        # Create middleware chain
        async def process_event(event: Event, middleware_index: int = 0) -> None:
            if middleware_index < len(self._middleware):
                # Process through middleware
                middleware = self._middleware[middleware_index]
                await middleware.process(
                    event,
                    lambda e: process_event(e, middleware_index + 1),
                )
            else:
                # Process with handlers
                handlers = self._handlers.get(event.event_type, set())
                for handler in handlers:
                    try:
                        await handler.handle_event(event)
                    except Exception as e:
                        logger.error(
                            "Handler error",
                            extra={
                                "event_type": event.event_type,
                                "handler": handler.__class__.__name__,
                                "error": str(e),
                            },
                            exc_info=True,
                        )

        # Start processing chain
        try:
            await process_event(event)
        except Exception as e:
            logger.error(
                "Event dispatch error",
                extra={
                    "event_type": event.event_type,
                    "error": str(e),
                },
                exc_info=True,
            )
