"""Metrics listener for event metrics collection.

This module provides a listener that collects metrics for events.
"""

from datetime import datetime

from pepperpy.core.metrics import Counter, Histogram, MetricsManager
from pepperpy.events.base import Event, EventListener
from pepperpy.monitoring import logger


class MetricsListener(EventListener):
    """Metrics event listener."""

    def __init__(self, name: str) -> None:
        """Initialize metrics listener.

        Args:
            name: Listener name
        """
        super().__init__(name)
        self._metrics = MetricsManager.get_instance()
        self._event_counters: dict[str, Counter] = {}
        self._error_counters: dict[str, Counter] = {}
        self._latency_histograms: dict[str, Histogram] = {}

    async def _initialize_listener(self) -> None:
        """Initialize metrics listener."""
        logger.info("Initializing metrics listener")

    async def _cleanup_listener(self) -> None:
        """Clean up metrics listener."""
        logger.info("Cleaning up metrics listener")
        self._event_counters.clear()
        self._error_counters.clear()
        self._latency_histograms.clear()

    async def notify(self, event: Event) -> None:
        """Handle event notification.

        Args:
            event: Event to handle
        """
        try:
            # Record event occurrence
            counter = await self._ensure_event_counter(event.type)
            counter.increment()

            # Record event latency
            start_time = datetime.utcnow()
            await super().notify(event)
            duration = (datetime.utcnow() - start_time).total_seconds()

            histogram = await self._ensure_latency_histogram(event.type)
            histogram.observe(duration)

        except Exception as e:
            # Record error
            counter = await self._ensure_error_counter(event.type)
            counter.increment()

            logger.error(f"Failed to handle event metrics: {e}")
            raise

    async def _ensure_event_counter(self, event_type: str) -> Counter:
        """Get or create event counter.

        Args:
            event_type: Event type

        Returns:
            Event counter
        """
        if event_type not in self._event_counters:
            self._event_counters[event_type] = self._metrics.create_counter(
                f"events_{event_type}_total",
                f"Total number of {event_type} events",
            )
        return self._event_counters[event_type]

    async def _ensure_error_counter(self, event_type: str) -> Counter:
        """Get or create error counter.

        Args:
            event_type: Event type

        Returns:
            Error counter
        """
        if event_type not in self._error_counters:
            self._error_counters[event_type] = self._metrics.create_counter(
                f"events_{event_type}_errors_total",
                f"Total number of {event_type} event errors",
            )
        return self._error_counters[event_type]

    async def _ensure_latency_histogram(self, event_type: str) -> Histogram:
        """Get or create latency histogram.

        Args:
            event_type: Event type

        Returns:
            Latency histogram
        """
        if event_type not in self._latency_histograms:
            self._latency_histograms[event_type] = self._metrics.create_histogram(
                f"events_{event_type}_latency_seconds",
                f"Latency of {event_type} event processing",
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )
        return self._latency_histograms[event_type]


# Export public API
__all__ = ["MetricsListener"]
