"""Event handlers base module.

This module provides base implementations for event handlers.
"""

import logging
from typing import Set

from pepperpy.core.base import ComponentBase
from pepperpy.core.metrics import Counter, Histogram
from pepperpy.events.types import (
    Event,
    EventHandler,
    EventType,
)

# Configure logging
logger = logging.getLogger(__name__)


class BaseEventHandler(ComponentBase, EventHandler):
    """Base event handler implementation.

    This class provides a base implementation for event handlers.
    """

    def __init__(self, event_types: Set[EventType]) -> None:
        """Initialize handler.

        Args:
            event_types: Event types to handle
        """
        super().__init__()
        self.event_types = event_types

        # Initialize metrics
        self._events_handled = Counter(
            "events_handled_total", "Total number of events handled"
        )
        self._event_errors = Counter(
            "event_errors_total", "Total number of event handling errors"
        )
        self._event_duration = Histogram(
            "event_duration_seconds", "Event handling duration in seconds"
        )

    def can_handle(self, event: Event) -> bool:
        """Check if handler can handle event.

        Args:
            event: Event to check

        Returns:
            bool: True if handler can handle event
        """
        return event.type in self.event_types

    async def handle(self, event: Event) -> None:
        """Handle event.

        Args:
            event: Event to handle
        """
        self._events_handled.inc()
        try:
            await self._handle_event(event)
        except Exception as e:
            self._event_errors.inc()
            logger.error(
                f"Failed to handle event: {e}",
                extra={
                    "event_type": event.type,
                    "source": event.source,
                },
                exc_info=True,
            )
            raise

    async def _handle_event(self, event: Event) -> None:
        """Handle event implementation.

        This method must be implemented by subclasses.

        Args:
            event: Event to handle
        """
        raise NotImplementedError("Event handling not implemented")


class SystemEventHandler(BaseEventHandler):
    """System event handler implementation.

    This class handles system-level events.
    """

    def __init__(self) -> None:
        """Initialize handler."""
        super().__init__({EventType.SYSTEM, EventType.LIFECYCLE})

    async def _handle_event(self, event: Event) -> None:
        """Handle system event.

        Args:
            event: Event to handle
        """
        action = event.metadata.get("action")
        status = event.metadata.get("status")

        logger.info(
            f"System event: {action} ({status})",
            extra={
                "source": event.source,
                "metadata": event.metadata,
            },
        )

        # Handle specific actions
        if action == "initialize":
            await self._handle_initialize(event)
        elif action == "cleanup":
            await self._handle_cleanup(event)
        elif action == "error":
            await self._handle_error(event)

    async def _handle_initialize(self, event: Event) -> None:
        """Handle system initialization.

        Args:
            event: Event to handle
        """
        logger.info(
            f"System initialized: {event.source}",
            extra={"metadata": event.metadata},
        )

    async def _handle_cleanup(self, event: Event) -> None:
        """Handle system cleanup.

        Args:
            event: Event to handle
        """
        logger.info(
            f"System cleaned up: {event.source}",
            extra={"metadata": event.metadata},
        )

    async def _handle_error(self, event: Event) -> None:
        """Handle system error.

        Args:
            event: Event to handle
        """
        logger.error(
            f"System error: {event.source}",
            extra={
                "error": event.error,
                "metadata": event.metadata,
            },
        )


class MetricsEventHandler(BaseEventHandler):
    """Metrics event handler implementation.

    This class handles metrics events.
    """

    def __init__(self) -> None:
        """Initialize handler."""
        super().__init__({EventType.METRIC})

    async def _handle_event(self, event: Event) -> None:
        """Handle metrics event.

        Args:
            event: Event to handle
        """
        metric_type = event.metadata.get("type")
        metric_name = event.metadata.get("name")
        metric_value = event.metadata.get("value")

        logger.debug(
            f"Metric: {metric_name}={metric_value} ({metric_type})",
            extra={
                "source": event.source,
                "metadata": event.metadata,
            },
        )


class LoggingEventHandler(BaseEventHandler):
    """Logging event handler implementation.

    This class handles logging events.
    """

    def __init__(self) -> None:
        """Initialize handler."""
        super().__init__({EventType.ERROR})

    async def _handle_event(self, event: Event) -> None:
        """Handle logging event.

        Args:
            event: Event to handle
        """
        level = event.metadata.get("level", "error").upper()
        message = event.metadata.get("message", str(event.error))

        # Convert string level to integer
        level_int = getattr(logging, level, logging.ERROR)

        logger.log(
            level_int,
            message,
            extra={
                "source": event.source,
                "metadata": event.metadata,
            },
            exc_info=event.error,
        )
