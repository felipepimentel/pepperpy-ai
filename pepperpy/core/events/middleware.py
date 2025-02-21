"""Event middleware implementations.

This module provides built-in event middleware:
- Audit middleware for security logging
- Metrics middleware for event metrics
- Validation middleware for event validation
- Retry middleware for event retries
"""

import logging
from datetime import datetime
from typing import Any, Callable

from pepperpy.core.events.base import Event, EventMiddleware
from pepperpy.monitoring import audit_logger, metrics

logger = logging.getLogger(__name__)


class AuditMiddleware(EventMiddleware):
    """Middleware for audit logging of events."""

    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event with audit logging.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result
        """
        # Log event before processing
        await audit_logger.log({
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp,
            "metadata": event.metadata,
        })

        try:
            # Process event
            result = await next_middleware(event)

            # Log success
            await audit_logger.log({
                "event_type": f"{event.event_type}.success",
                "source": event.source,
                "timestamp": datetime.utcnow(),
                "metadata": event.metadata,
                "result": str(result),
            })

            return result

        except Exception as e:
            # Log failure
            await audit_logger.log({
                "event_type": f"{event.event_type}.failure",
                "source": event.source,
                "timestamp": datetime.utcnow(),
                "metadata": event.metadata,
                "error": str(e),
            })
            raise


class MetricsMiddleware(EventMiddleware):
    """Middleware for collecting event metrics."""

    def __init__(self) -> None:
        """Initialize metrics middleware."""
        self.event_counter = metrics.Counter(
            "events_total",
            "Total number of events processed",
            ["event_type", "source", "status"],
        )
        self.event_duration = metrics.Histogram(
            "event_duration_seconds",
            "Event processing duration in seconds",
            ["event_type", "source"],
        )

    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event with metrics collection.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result
        """
        start_time = datetime.utcnow()

        try:
            # Process event
            result = await next_middleware(event)

            # Record success metrics
            self.event_counter.inc(
                labels={
                    "event_type": event.event_type,
                    "source": event.source,
                    "status": "success",
                }
            )

            return result

        except Exception:
            # Record failure metrics
            self.event_counter.inc(
                labels={
                    "event_type": event.event_type,
                    "source": event.source,
                    "status": "failure",
                }
            )
            raise

        finally:
            # Record duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.event_duration.observe(
                duration,
                labels={
                    "event_type": event.event_type,
                    "source": event.source,
                },
            )


class ValidationMiddleware(EventMiddleware):
    """Middleware for event validation."""

    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event with validation.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result

        Raises:
            ValidationError: If event validation fails
        """
        # Validate event type
        if not event.event_type:
            raise ValueError("Event type is required")

        # Validate source
        if not event.source:
            raise ValueError("Event source is required")

        # Validate timestamp
        if not event.timestamp:
            raise ValueError("Event timestamp is required")

        # Process event
        return await next_middleware(event)


class RetryMiddleware(EventMiddleware):
    """Middleware for event retries."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
    ) -> None:
        """Initialize retry middleware.

        Args:
            max_retries: Maximum number of retries
            retry_delay: Initial delay between retries in seconds
            exponential_backoff: Whether to use exponential backoff
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff

    async def process(
        self, event: Event, next_middleware: Callable[[Event], Any]
    ) -> Any:
        """Process event with retries.

        Args:
            event: Event to process
            next_middleware: Next middleware in chain

        Returns:
            Any: Processing result
        """
        retries = 0
        last_error = None

        while retries <= self.max_retries:
            try:
                return await next_middleware(event)
            except Exception as e:
                last_error = e
                retries += 1

                if retries <= self.max_retries:
                    # Calculate delay
                    delay = (
                        self.retry_delay * (2 ** (retries - 1))
                        if self.exponential_backoff
                        else self.retry_delay
                    )

                    # Log retry attempt
                    logger.warning(
                        f"Event processing failed, retrying in {delay}s",
                        extra={
                            "event_type": event.event_type,
                            "source": event.source,
                            "retry": retries,
                            "error": str(e),
                        },
                    )

                    # Wait before retry
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "Event processing failed after max retries",
                        extra={
                            "event_type": event.event_type,
                            "source": event.source,
                            "retries": retries,
                            "error": str(e),
                        },
                    )
                    raise last_error
