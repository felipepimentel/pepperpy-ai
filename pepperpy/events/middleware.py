"""Event middleware implementations.

This module provides middleware components for the event system:
- Logging middleware
- Metrics middleware
- Validation middleware
- Rate limiting middleware
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pepperpy.core.errors import ValidationError
from pepperpy.events.base import Event, EventMiddleware
from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager


class LoggingMiddleware(EventMiddleware):
    """Middleware for event logging."""

    def __init__(self, log_level: str = "INFO") -> None:
        """Initialize logging middleware.

        Args:
            log_level: Logging level to use
        """
        self._log_level = getattr(logging, log_level.upper())

    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event through logging middleware.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result
        """
        logger.log(
            self._log_level,
            f"Processing event: {event.event_type}",
            extra={
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "source": event.source,
                "metadata": event.metadata,
            },
        )

        try:
            result = await next_middleware(event)
            logger.log(
                self._log_level,
                f"Event processed: {event.event_type}",
                extra={
                    "event_id": str(event.event_id),
                    "event_type": event.event_type,
                    "source": event.source,
                },
            )
            return result
        except Exception as e:
            logger.error(
                f"Error processing event: {event.event_type}",
                extra={
                    "event_id": str(event.event_id),
                    "event_type": event.event_type,
                    "source": event.source,
                    "error": str(e),
                },
            )
            raise


class MetricsMiddleware(EventMiddleware):
    """Middleware for event metrics collection."""

    def __init__(self) -> None:
        """Initialize metrics middleware."""
        self._metrics = MetricsManager.get_instance()
        self._event_counters: dict[str, Counter] = {}
        self._error_counters: dict[str, Counter] = {}
        self._latency_histograms: dict[str, Histogram] = {}

    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event through metrics middleware.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result
        """
        # Record event
        counter = await self._ensure_event_counter(event.event_type)
        await counter.inc()

        # Track latency
        start_time = datetime.utcnow()

        try:
            result = await next_middleware(event)

            # Record latency
            duration = (datetime.utcnow() - start_time).total_seconds()
            histogram = await self._ensure_latency_histogram(event.event_type)
            await histogram.observe(duration)

            return result
        except Exception:
            # Record error
            error_counter = await self._ensure_error_counter(event.event_type)
            await error_counter.inc()
            raise

    async def _ensure_event_counter(self, event_type: str) -> Counter:
        """Get or create event counter.

        Args:
            event_type: Type of event

        Returns:
            Event counter
        """
        if event_type not in self._event_counters:
            self._event_counters[event_type] = await self._metrics.create_counter(
                name=f"events_{event_type}_total",
                description=f"Total number of {event_type} events",
            )
        return self._event_counters[event_type]

    async def _ensure_error_counter(self, event_type: str) -> Counter:
        """Get or create error counter.

        Args:
            event_type: Type of event

        Returns:
            Error counter
        """
        if event_type not in self._error_counters:
            self._error_counters[event_type] = await self._metrics.create_counter(
                name=f"events_{event_type}_errors_total",
                description=f"Total number of {event_type} event errors",
            )
        return self._error_counters[event_type]

    async def _ensure_latency_histogram(self, event_type: str) -> Histogram:
        """Get or create latency histogram.

        Args:
            event_type: Type of event

        Returns:
            Latency histogram
        """
        if event_type not in self._latency_histograms:
            self._latency_histograms[event_type] = await self._metrics.create_histogram(
                name=f"events_{event_type}_latency_seconds",
                description=f"Latency of {event_type} event processing",
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )
        return self._latency_histograms[event_type]


class ValidationMiddleware(EventMiddleware):
    """Middleware for event validation."""

    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event through validation middleware.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result

        Raises:
            ValidationError: If event validation fails
        """
        # Validate required fields
        if not event.event_type:
            raise ValidationError("Event type is required")
        if not event.source:
            raise ValidationError("Event source is required")

        # Validate event type format
        if "." in event.event_type:
            parts = event.event_type.split(".")
            if not all(parts):
                raise ValidationError("Invalid event type format")

        return await next_middleware(event)


class RateLimitingMiddleware(EventMiddleware):
    """Middleware for event rate limiting."""

    def __init__(self, max_events: int = 100, window_seconds: float = 60.0) -> None:
        """Initialize rate limiting middleware.

        Args:
            max_events: Maximum events per window
            window_seconds: Window size in seconds
        """
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._events: dict[str, list[datetime]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event through rate limiting middleware.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result

        Raises:
            ValidationError: If rate limit is exceeded
        """
        # Get or create lock for event type
        if event.event_type not in self._locks:
            self._locks[event.event_type] = asyncio.Lock()

        async with self._locks[event.event_type]:
            # Initialize event list if needed
            if event.event_type not in self._events:
                self._events[event.event_type] = []

            # Remove old events
            now = datetime.utcnow()
            cutoff = now.timestamp() - self._window_seconds
            self._events[event.event_type] = [
                ts for ts in self._events[event.event_type] if ts.timestamp() > cutoff
            ]

            # Check rate limit
            if len(self._events[event.event_type]) >= self._max_events:
                raise ValidationError(
                    f"Rate limit exceeded for event type: {event.event_type}"
                )

            # Add current event
            self._events[event.event_type].append(now)

            # Process event
            return await next_middleware(event)
