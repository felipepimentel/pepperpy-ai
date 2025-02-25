"""Event management system.

This module provides event management functionality:
- Event registration and dispatch
- Event filtering and routing
- Event monitoring and metrics
- Event lifecycle management
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar

from pepperpy.core.errors import EventError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variable for event data
T = TypeVar("T")


@dataclass
class Event:
    """Base event class."""

    type: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventHandler:
    """Event handler information."""

    callback: Callable[[Event], Awaitable[None]]
    filters: set[str] | None = None
    priority: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0


class EventManager(LifecycleComponent):
    """Manager for event lifecycle."""

    def __init__(self) -> None:
        """Initialize manager."""
        super().__init__("event_manager")
        self._handlers: dict[str, list[EventHandler]] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """Initialize manager.

        Raises:
            EventError: If initialization fails
        """
        self._initialized = True
        logger.info("Event manager initialized")

    async def _cleanup(self) -> None:
        """Clean up manager.

        Raises:
            EventError: If cleanup fails
        """
        self._initialized = False
        logger.info("Event manager cleaned up")

    def register_handler(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Register an event handler.

        Args:
            event_type: Event type to handle
            handler: Event handler

        Raises:
            EventError: If registration fails
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        handlers = self._handlers[event_type]
        handlers.append(handler)
        handlers.sort(key=lambda h: h.priority, reverse=True)

        logger.info(
            "Event handler registered",
            extra={
                "event_type": event_type,
                "priority": handler.priority,
            },
        )

    def unregister_handler(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Unregister an event handler.

        Args:
            event_type: Event type
            handler: Event handler

        Raises:
            EventError: If unregistration fails
        """
        if event_type not in self._handlers:
            raise EventError(f"No handlers registered for {event_type}")

        handlers = self._handlers[event_type]
        try:
            handlers.remove(handler)
            if not handlers:
                del self._handlers[event_type]

            logger.info(
                "Event handler unregistered",
                extra={
                    "event_type": event_type,
                    "priority": handler.priority,
                },
            )
        except ValueError:
            raise EventError(f"Handler not found for {event_type}")

    async def dispatch(
        self,
        event: Event,
        wait: bool = True,
    ) -> None:
        """Dispatch an event.

        Args:
            event: Event to dispatch
            wait: Whether to wait for handlers to complete

        Raises:
            EventError: If dispatch fails
        """
        if not self._initialized:
            raise EventError("Event manager not initialized")

        handlers = self._handlers.get(event.type, [])
        if not handlers:
            logger.debug(f"No handlers for event type: {event.type}")
            return

        tasks = []
        for handler in handlers:
            if handler.filters and not any(
                f in event.metadata for f in handler.filters
            ):
                continue

            task = asyncio.create_task(self._handle_event(event, handler))
            tasks.append(task)

            if not wait:
                task.add_done_callback(self._handle_task_result)

        if wait:
            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                raise EventError(f"Event dispatch failed: {e}")

    def list_handlers(
        self, event_type: str | None = None
    ) -> dict[str, list[EventHandler]]:
        """List registered handlers.

        Args:
            event_type: Optional event type filter

        Returns:
            dict[str, list[EventHandler]]: Mapping of event types to handlers
        """
        if event_type:
            return {event_type: self._handlers.get(event_type, [])}
        return self._handlers.copy()

    async def _handle_event(
        self,
        event: Event,
        handler: EventHandler,
    ) -> None:
        """Handle an event.

        Args:
            event: Event to handle
            handler: Event handler

        Raises:
            EventError: If handling fails
        """
        retries = 0
        while True:
            try:
                await handler.callback(event)
                break
            except Exception as e:
                retries += 1
                if retries >= handler.max_retries:
                    logger.error(
                        "Event handler failed",
                        extra={
                            "event_type": event.type,
                            "error": str(e),
                            "retries": retries,
                        },
                    )
                    raise EventError(
                        f"Event handler failed after {retries} retries: {e}"
                    )

                logger.warning(
                    "Event handler failed, retrying",
                    extra={
                        "event_type": event.type,
                        "error": str(e),
                        "retry": retries,
                    },
                )
                await asyncio.sleep(handler.retry_delay)

    def _handle_task_result(self, task: asyncio.Task) -> None:
        """Handle background task result.

        Args:
            task: Completed task
        """
        try:
            task.result()
        except Exception as e:
            logger.error("Background task failed", extra={"error": str(e)})


__all__ = [
    "Event",
    "EventHandler",
    "EventManager",
]
