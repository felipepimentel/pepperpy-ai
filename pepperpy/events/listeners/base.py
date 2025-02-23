"""Event listeners base module.

This module provides base implementations for event listeners.
"""

import asyncio
import logging
from typing import Set

from pepperpy.core.base import ComponentBase
from pepperpy.core.metrics import Counter, Histogram
from pepperpy.events.types import (
    Event,
    EventListener,
    EventType,
)

# Configure logging
logger = logging.getLogger(__name__)


class BaseEventListener(ComponentBase, EventListener):
    """Base event listener implementation.

    This class provides a base implementation for event listeners.
    """

    def __init__(self, event_types: Set[EventType]) -> None:
        """Initialize listener.

        Args:
            event_types: Event types to listen for
        """
        super().__init__()
        self.event_types = event_types
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False

        # Initialize metrics
        self._events_received = Counter(
            "events_received_total", "Total number of events received"
        )
        self._event_errors = Counter(
            "event_errors_total", "Total number of event processing errors"
        )
        self._event_duration = Histogram(
            "event_duration_seconds", "Event processing duration in seconds"
        )

    def can_handle(self, event: Event) -> bool:
        """Check if listener can handle event.

        Args:
            event: Event to check

        Returns:
            bool: True if listener can handle event
        """
        return event.type in self.event_types

    async def on_event(self, event: Event) -> None:
        """Handle event.

        Args:
            event: Event to handle
        """
        self._events_received.inc()
        await self._queue.put(event)

    async def start(self) -> None:
        """Start event processing."""
        self._running = True
        while self._running:
            try:
                event = await self._queue.get()
                await self._process_event(event)
                self._queue.task_done()
            except Exception as e:
                self._event_errors.inc()
                logger.error(
                    f"Failed to process event: {e}",
                    extra={
                        "event_type": event.type,
                        "source": event.source,
                    },
                    exc_info=True,
                )

    async def stop(self) -> None:
        """Stop event processing."""
        self._running = False
        await self._queue.join()

    async def _process_event(self, event: Event) -> None:
        """Process event implementation.

        This method must be implemented by subclasses.

        Args:
            event: Event to process
        """
        raise NotImplementedError("Event processing not implemented")


class MetricsListener(BaseEventListener):
    """Metrics listener implementation.

    This class listens for metrics events and updates metrics.
    """

    def __init__(self) -> None:
        """Initialize listener."""
        super().__init__({EventType.METRIC})

    async def _process_event(self, event: Event) -> None:
        """Process metrics event.

        Args:
            event: Event to process
        """
        metric_type = event.metadata.get("type", "")
        metric_name = event.metadata.get("name", "")
        metric_value = event.metadata.get("value", 0.0)

        # Validate required fields
        if not metric_name or not isinstance(metric_name, str):
            logger.error("Invalid metric name", extra={"metadata": event.metadata})
            return

        if not isinstance(metric_value, (int, float)):
            logger.error("Invalid metric value", extra={"metadata": event.metadata})
            return

        logger.debug(
            f"Processing metric: {metric_name}={metric_value} ({metric_type})",
            extra={
                "source": event.source,
                "metadata": event.metadata,
            },
        )

        # Convert value to float
        value = float(metric_value)

        # Update metrics based on type
        if metric_type == "counter":
            self._update_counter(metric_name, value)
        elif metric_type == "gauge":
            self._update_gauge(metric_name, value)
        elif metric_type == "histogram":
            self._update_histogram(metric_name, value)

    def _update_counter(self, name: str, value: float) -> None:
        """Update counter metric.

        Args:
            name: Metric name
            value: Metric value
        """
        counter = Counter(name, f"Counter metric: {name}")
        counter.inc(value)

    def _update_gauge(self, name: str, value: float) -> None:
        """Update gauge metric.

        Args:
            name: Metric name
            value: Metric value
        """
        # TODO: Implement gauge metrics

    def _update_histogram(self, name: str, value: float) -> None:
        """Update histogram metric.

        Args:
            name: Metric name
            value: Metric value
        """
        histogram = Histogram(name, f"Histogram metric: {name}")
        histogram.observe(value)


class LoggingListener(BaseEventListener):
    """Logging listener implementation.

    This class listens for logging events and logs messages.
    """

    def __init__(self) -> None:
        """Initialize listener."""
        super().__init__({EventType.ERROR})

    async def _process_event(self, event: Event) -> None:
        """Process logging event.

        Args:
            event: Event to process
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
