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
    """Manages events and their lifecycle."""

    def __init__(self) -> None:
        """Initialize event manager."""
        super().__init__("event_manager")
        self._handlers: dict[str, list[EventHandler]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize event manager.

        Raises:
            EventError: If initialization fails
        """
        try:
            await super().initialize()
            self._initialized = True
            logger.info("Event manager initialized")
        except Exception as e:
            raise EventError(f"Failed to initialize event manager: {e}")

    async def cleanup(self) -> None:
        """Clean up event manager.

        Raises:
            EventError: If cleanup fails
        """
        try:
            await super().cleanup()
            self._initialized = False
            logger.info("Event manager cleaned up")
        except Exception as e:
            raise EventError(f"Failed to clean up event manager: {e}")

    def register_handler(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Register event handler.

        Args:
            event_type: Event type
            handler: Event handler

        Raises:
            EventError: If registration fails
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        # Insert handler in priority order
        handlers = self._handlers[event_type]
        index = 0
        while index < len(handlers) and handlers[index].priority >= handler.priority:
            index += 1
        handlers.insert(index, handler)

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
        """Unregister event handler.

        Args:
            event_type: Event type
            handler: Event handler

        Raises:
            EventError: If unregistration fails
        """
        if event_type not in self._handlers:
            raise EventError(f"Unknown event type {event_type}")

        try:
            self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]
            logger.info(
                "Event handler unregistered",
                extra={"event_type": event_type},
            )
        except ValueError:
            raise EventError(f"Handler not found for event type {event_type}")

    async def dispatch(
        self,
        event: Event,
        wait: bool = True,
    ) -> None:
        """Dispatch event to handlers.

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
            logger.warning(
                "No handlers found for event",
                extra={"event_type": event.type},
            )
            return

        tasks = []
        for handler in handlers:
            if handler.filters and not any(
                f in event.metadata for f in handler.filters
            ):
                continue

            task = asyncio.create_task(self._handle_event(event, handler))
            tasks.append(task)

        if wait:
            await asyncio.gather(*tasks)
        else:
            # Let tasks run in background
            for task in tasks:
                task.add_done_callback(self._handle_task_result)

    def list_handlers(
        self, event_type: str | None = None
    ) -> dict[str, list[EventHandler]]:
        """List registered handlers.

        Args:
            event_type: Optional event type filter

        Returns:
            Dictionary of event types to handlers
        """
        if event_type:
            return {event_type: self._handlers.get(event_type, [])}
        return self._handlers.copy()

    async def _handle_event(
        self,
        event: Event,
        handler: EventHandler,
    ) -> None:
        """Handle event with retries.

        Args:
            event: Event to handle
            handler: Event handler

        Raises:
            EventError: If handling fails after retries
        """
        for attempt in range(handler.max_retries):
            try:
                await handler.callback(event)
                return
            except Exception as e:
                if attempt == handler.max_retries - 1:
                    logger.error(
                        "Event handler failed",
                        extra={
                            "event_type": event.type,
                            "error": str(e),
                            "attempts": attempt + 1,
                        },
                    )
                    raise EventError(
                        f"Event handler failed after {attempt + 1} attempts: {e}"
                    )
                else:
                    logger.warning(
                        "Event handler failed, retrying",
                        extra={
                            "event_type": event.type,
                            "error": str(e),
                            "attempt": attempt + 1,
                            "retry_delay": handler.retry_delay,
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
            logger.error(
                "Background event handler failed",
                extra={"error": str(e)},
            )
