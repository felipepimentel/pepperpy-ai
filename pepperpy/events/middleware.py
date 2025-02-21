"""Event processing middleware.

This module provides middleware components for event processing:
- Base middleware interface
- Audit middleware for security and monitoring
- Error handling middleware
- Metrics middleware
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Awaitable, Callable

from pepperpy.events.base import Event
from pepperpy.monitoring import logger, metrics

# Configure logging
logger = logger.getChild(__name__)

# Type alias for middleware next function
NextMiddleware = Callable[[Event], Awaitable[None]]


class EventMiddleware(ABC):
    """Base class for event processing middleware."""

    async def initialize(self) -> None:
        """Initialize middleware resources.

        This method should be overridden by middleware implementations
        that need initialization.
        """
        pass

    @abstractmethod
    async def process(self, event: Event, next_middleware: NextMiddleware) -> None:
        """Process an event and pass it to the next middleware.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain to call

        Raises:
            Exception: If middleware processing fails
        """
        pass


class AuditMiddleware(EventMiddleware):
    """Middleware for auditing events."""

    def __init__(self) -> None:
        """Initialize audit middleware."""
        self._audit_counter = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize metrics."""
        if self._initialized:
            return

        metrics_manager = metrics.MetricsManager.get_instance()
        self._audit_counter = await metrics_manager.create_counter(
            "event_audits_total",
            "Total number of audited events",
            labels={"type": "audit"},
        )
        self._initialized = True

    async def process(self, event: Event, next_middleware: NextMiddleware) -> None:
        """Audit event and pass to next middleware.

        Args:
            event: Event to audit
            next_middleware: Next middleware to call
        """
        # Record audit
        if self._audit_counter:
            self._audit_counter.record(1)

        # Log audit details
        logger.info(
            "Event audit",
            extra={
                "event_type": event.event_type,
                "event_id": str(event.event_id),
                "timestamp": event.timestamp.isoformat(),
                "priority": event.priority.name,
            },
        )

        # Pass to next middleware
        await next_middleware(event)


class ErrorHandlingMiddleware(EventMiddleware):
    """Middleware for handling errors during event processing."""

    def __init__(self) -> None:
        """Initialize error handling middleware."""
        self._error_counter = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize metrics."""
        if self._initialized:
            return

        metrics_manager = metrics.MetricsManager.get_instance()
        self._error_counter = await metrics_manager.create_counter(
            "event_errors_total",
            "Total number of event processing errors",
            labels={"type": "error"},
        )
        self._initialized = True

    async def process(self, event: Event, next_middleware: NextMiddleware) -> None:
        """Handle errors during event processing.

        Args:
            event: Event being processed
            next_middleware: Next middleware to call

        Raises:
            Exception: Re-raises handled exceptions after logging
        """
        try:
            await next_middleware(event)
        except Exception as e:
            if self._error_counter:
                self._error_counter.record(1)

            logger.error(
                "Error processing event",
                extra={
                    "event_type": event.event_type,
                    "event_id": str(event.event_id),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise


class MetricsMiddleware(EventMiddleware):
    """Middleware for collecting event processing metrics."""

    def __init__(self) -> None:
        """Initialize metrics middleware."""
        self._latency_histogram = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize metrics."""
        if self._initialized:
            return

        metrics_manager = metrics.MetricsManager.get_instance()
        self._latency_histogram = await metrics_manager.create_histogram(
            "event_processing_duration_seconds",
            "Event processing duration in seconds",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels={"type": "processing"},
        )
        self._initialized = True

    async def process(self, event: Event, next_middleware: NextMiddleware) -> None:
        """Collect metrics during event processing.

        Args:
            event: Event being processed
            next_middleware: Next middleware to call
        """
        start_time = datetime.utcnow()

        try:
            await next_middleware(event)
        finally:
            # Record processing duration
            if self._latency_histogram:
                duration = (datetime.utcnow() - start_time).total_seconds()
                self._latency_histogram.record(duration)
