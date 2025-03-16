"""Provider telemetry and monitoring system for PepperPy.

This module provides a telemetry and monitoring system for PepperPy providers,
allowing providers to report metrics, events, and logs to a central system.
This helps with debugging, performance monitoring, and usage tracking.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.utils import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"  # Metrics that increment or decrement
    GAUGE = "gauge"  # Metrics that can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Statistical summary of values
    TIMER = "timer"  # Duration of operations


class EventLevel(Enum):
    """Levels for events that can be reported."""

    DEBUG = "debug"  # Detailed information for debugging
    INFO = "info"  # General information about system operation
    WARNING = "warning"  # Potential issues that don't affect operation
    ERROR = "error"  # Errors that affect operation but don't cause failure
    CRITICAL = "critical"  # Critical errors that cause system failure


@dataclass
class Metric:
    """A metric that can be reported by providers.

    This class represents a metric that can be reported by providers,
    such as request count, latency, or error rate.
    """

    name: str
    type: MetricType
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Initialize the metric with a timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Event:
    """An event that can be reported by providers.

    This class represents an event that can be reported by providers,
    such as a request, an error, or a system state change.
    """

    name: str
    level: EventLevel
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Initialize the event with a timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


class TelemetryHandler:
    """Base class for telemetry handlers.

    Telemetry handlers are responsible for processing metrics and events.
    """

    def handle_metric(self, metric: Metric) -> None:
        """Handle a metric.

        Args:
            metric: The metric to handle
        """
        pass

    def handle_event(self, event: Event) -> None:
        """Handle an event.

        Args:
            event: The event to handle
        """
        pass


class LoggingTelemetryHandler(TelemetryHandler):
    """Telemetry handler that logs metrics and events.

    This handler logs metrics and events to the Python logging system.
    """

    def handle_metric(self, metric: Metric) -> None:
        """Handle a metric by logging it.

        Args:
            metric: The metric to handle
        """
        tags_str = " ".join(f"{k}={v}" for k, v in metric.tags.items())
        logger.info(
            f"METRIC {metric.name}={metric.value} type={metric.type.value} {tags_str}"
        )

    def handle_event(self, event: Event) -> None:
        """Handle an event by logging it.

        Args:
            event: The event to handle
        """
        log_level = getattr(logging, event.level.value.upper())
        tags_str = " ".join(f"{k}={v}" for k, v in event.tags.items())
        data_str = " ".join(f"{k}={v}" for k, v in event.data.items())
        logger.log(
            log_level,
            f"EVENT {event.name} level={event.level.value} {tags_str} {data_str} - {event.message}",
        )


class CompositeTelemetryHandler(TelemetryHandler):
    """Telemetry handler that delegates to multiple handlers.

    This handler delegates to multiple handlers, allowing metrics and events
    to be processed by multiple systems.
    """

    def __init__(self, handlers: List[TelemetryHandler]):
        """Initialize the composite handler.

        Args:
            handlers: The handlers to delegate to
        """
        self.handlers = handlers

    def handle_metric(self, metric: Metric) -> None:
        """Handle a metric by delegating to all handlers.

        Args:
            metric: The metric to handle
        """
        for handler in self.handlers:
            try:
                handler.handle_metric(metric)
            except Exception as e:
                logger.error(
                    f"Error handling metric in {handler.__class__.__name__}: {e}"
                )

    def handle_event(self, event: Event) -> None:
        """Handle an event by delegating to all handlers.

        Args:
            event: The event to handle
        """
        for handler in self.handlers:
            try:
                handler.handle_event(event)
            except Exception as e:
                logger.error(
                    f"Error handling event in {handler.__class__.__name__}: {e}"
                )


class TelemetryManager:
    """Manager for telemetry handlers.

    This class manages telemetry handlers and provides methods for reporting
    metrics and events. It's the main entry point for the telemetry system.
    """

    _instance: Optional["TelemetryManager"] = None
    _handlers: Dict[str, TelemetryHandler] = {}
    _default_handler: Optional[TelemetryHandler] = None
    _enabled: bool = True

    @classmethod
    def get_instance(cls) -> "TelemetryManager":
        """Get the singleton instance of the telemetry manager.

        Returns:
            The telemetry manager instance
        """
        if cls._instance is None:
            cls._instance = TelemetryManager()
        return cls._instance

    def register_handler(self, name: str, handler: TelemetryHandler) -> None:
        """Register a telemetry handler.

        Args:
            name: The name of the handler
            handler: The handler to register
        """
        self._handlers[name] = handler
        if self._default_handler is None:
            self._default_handler = handler

    def set_default_handler(self, name: str) -> None:
        """Set the default telemetry handler.

        Args:
            name: The name of the handler to set as default

        Raises:
            ValueError: If the handler is not registered
        """
        if name not in self._handlers:
            raise ValueError(f"Handler {name} is not registered")
        self._default_handler = self._handlers[name]

    def get_handler(self, name: Optional[str] = None) -> TelemetryHandler:
        """Get a telemetry handler.

        Args:
            name: The name of the handler to get, or None for the default handler

        Returns:
            The telemetry handler

        Raises:
            ValueError: If the handler is not registered or no default handler is set
        """
        if name is None:
            if self._default_handler is None:
                raise ValueError("No default handler is set")
            return self._default_handler

        if name not in self._handlers:
            raise ValueError(f"Handler {name} is not registered")
        return self._handlers[name]

    def report_metric(
        self,
        name: str,
        value: float,
        type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a metric.

        Args:
            name: The name of the metric
            value: The value of the metric
            type: The type of the metric
            tags: Optional tags for the metric
            handler_name: The name of the handler to use, or None for the default handler
        """
        if not self._enabled:
            return

        metric = Metric(
            name=name,
            value=value,
            type=type,
            tags=tags or {},
        )

        try:
            handler = self.get_handler(handler_name)
            handler.handle_metric(metric)
        except Exception as e:
            logger.error(f"Error reporting metric {name}: {e}")

    def report_event(
        self,
        name: str,
        level: EventLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report an event.

        Args:
            name: The name of the event
            level: The level of the event
            message: The message of the event
            data: Optional data for the event
            tags: Optional tags for the event
            handler_name: The name of the handler to use, or None for the default handler
        """
        if not self._enabled:
            return

        event = Event(
            name=name,
            level=level,
            message=message,
            data=data or {},
            tags=tags or {},
        )

        try:
            handler = self.get_handler(handler_name)
            handler.handle_event(event)
        except Exception as e:
            logger.error(f"Error reporting event {name}: {e}")

    def enable(self) -> None:
        """Enable telemetry."""
        self._enabled = True

    def disable(self) -> None:
        """Disable telemetry."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if telemetry is enabled.

        Returns:
            True if telemetry is enabled, False otherwise
        """
        return self._enabled


class ProviderTelemetry:
    """Telemetry for a specific provider.

    This class provides telemetry methods for a specific provider.
    """

    def __init__(self, provider_id: str):
        """Initialize the provider telemetry.

        Args:
            provider_id: The ID of the provider
        """
        self.provider_id = provider_id
        self.manager = TelemetryManager.get_instance()

    def report_metric(
        self,
        name: str,
        value: float,
        type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a metric.

        Args:
            name: The name of the metric
            value: The value of the metric
            type: The type of the metric
            tags: Optional tags for the metric
            handler_name: The name of the handler to use, or None for the default handler
        """
        # Add provider ID to tags
        tags = tags or {}
        tags["provider_id"] = self.provider_id

        self.manager.report_metric(
            name=name,
            value=value,
            type=type,
            tags=tags,
            handler_name=handler_name,
        )

    def report_event(
        self,
        name: str,
        level: EventLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report an event.

        Args:
            name: The name of the event
            level: The level of the event
            message: The message of the event
            data: Optional data for the event
            tags: Optional tags for the event
            handler_name: The name of the handler to use, or None for the default handler
        """
        # Add provider ID to tags
        tags = tags or {}
        tags["provider_id"] = self.provider_id

        self.manager.report_event(
            name=name,
            level=level,
            message=message,
            data=data,
            tags=tags,
            handler_name=handler_name,
        )

    def count(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a counter metric.

        Args:
            name: The name of the metric
            value: The value to increment the counter by
            tags: Optional tags for the metric
            handler_name: The name of the handler to use, or None for the default handler
        """
        self.report_metric(
            name=name,
            value=value,
            type=MetricType.COUNTER,
            tags=tags,
            handler_name=handler_name,
        )

    def gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a gauge metric.

        Args:
            name: The name of the metric
            value: The value of the gauge
            tags: Optional tags for the metric
            handler_name: The name of the handler to use, or None for the default handler
        """
        self.report_metric(
            name=name,
            value=value,
            type=MetricType.GAUGE,
            tags=tags,
            handler_name=handler_name,
        )

    def histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a histogram metric.

        Args:
            name: The name of the metric
            value: The value to add to the histogram
            tags: Optional tags for the metric
            handler_name: The name of the handler to use, or None for the default handler
        """
        self.report_metric(
            name=name,
            value=value,
            type=MetricType.HISTOGRAM,
            tags=tags,
            handler_name=handler_name,
        )

    def time(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> "Timer":
        """Create a timer for measuring operation duration.

        Args:
            name: The name of the timer metric
            tags: Optional tags for the metric
            handler_name: The name of the handler to use, or None for the default handler

        Returns:
            A timer context manager
        """
        return Timer(
            telemetry=self,
            name=name,
            tags=tags,
            handler_name=handler_name,
        )

    def debug(
        self,
        name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a debug event.

        Args:
            name: The name of the event
            message: The message of the event
            data: Optional data for the event
            tags: Optional tags for the event
            handler_name: The name of the handler to use, or None for the default handler
        """
        self.report_event(
            name=name,
            level=EventLevel.DEBUG,
            message=message,
            data=data,
            tags=tags,
            handler_name=handler_name,
        )

    def info(
        self,
        name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report an info event.

        Args:
            name: The name of the event
            message: The message of the event
            data: Optional data for the event
            tags: Optional tags for the event
            handler_name: The name of the handler to use, or None for the default handler
        """
        self.report_event(
            name=name,
            level=EventLevel.INFO,
            message=message,
            data=data,
            tags=tags,
            handler_name=handler_name,
        )

    def warning(
        self,
        name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a warning event.

        Args:
            name: The name of the event
            message: The message of the event
            data: Optional data for the event
            tags: Optional tags for the event
            handler_name: The name of the handler to use, or None for the default handler
        """
        self.report_event(
            name=name,
            level=EventLevel.WARNING,
            message=message,
            data=data,
            tags=tags,
            handler_name=handler_name,
        )

    def error(
        self,
        name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report an error event.

        Args:
            name: The name of the event
            message: The message of the event
            data: Optional data for the event
            tags: Optional tags for the event
            handler_name: The name of the handler to use, or None for the default handler
        """
        self.report_event(
            name=name,
            level=EventLevel.ERROR,
            message=message,
            data=data,
            tags=tags,
            handler_name=handler_name,
        )

    def critical(
        self,
        name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a critical event.

        Args:
            name: The name of the event
            message: The message of the event
            data: Optional data for the event
            tags: Optional tags for the event
            handler_name: The name of the handler to use, or None for the default handler
        """
        self.report_event(
            name=name,
            level=EventLevel.CRITICAL,
            message=message,
            data=data,
            tags=tags,
            handler_name=handler_name,
        )


class Timer:
    """Context manager for timing operations.

    This class provides a context manager for timing operations and reporting
    the duration as a metric.

    Example:
        ```python
        telemetry = get_provider_telemetry("my_provider")
        with telemetry.time("operation_duration"):
            # Do something
        ```
    """

    def __init__(
        self,
        telemetry: ProviderTelemetry,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ):
        """Initialize the timer.

        Args:
            telemetry: The provider telemetry to report to
            name: The name of the timer metric
            tags: Optional tags for the metric
            handler_name: The name of the handler to use, or None for the default handler
        """
        self.telemetry = telemetry
        self.name = name
        self.tags = tags
        self.handler_name = handler_name
        self.start_time = 0.0
        self.end_time = 0.0

    def __enter__(self) -> "Timer":
        """Enter the context.

        Returns:
            The timer instance
        """
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised
        """
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        # Report the duration as a timer metric
        self.telemetry.report_metric(
            name=self.name,
            value=duration,
            type=MetricType.TIMER,
            tags=self.tags,
            handler_name=self.handler_name,
        )


def initialize_telemetry() -> None:
    """Initialize the telemetry system.

    This function initializes the telemetry system with a default logging handler.
    It should be called once at the start of the application.
    """
    manager = TelemetryManager.get_instance()

    # Register a default logging handler
    logging_handler = LoggingTelemetryHandler()
    manager.register_handler("logging", logging_handler)
    manager.set_default_handler("logging")


def get_provider_telemetry(provider_id: str) -> ProviderTelemetry:
    """Get telemetry for a specific provider.

    Args:
        provider_id: The ID of the provider

    Returns:
        A provider telemetry instance
    """
    return ProviderTelemetry(provider_id)


def report_metric(
    name: str,
    value: float,
    type: MetricType,
    tags: Optional[Dict[str, str]] = None,
    handler_name: Optional[str] = None,
) -> None:
    """Report a metric.

    Args:
        name: The name of the metric
        value: The value of the metric
        type: The type of the metric
        tags: Optional tags for the metric
        handler_name: The name of the handler to use, or None for the default handler
    """
    manager = TelemetryManager.get_instance()
    manager.report_metric(
        name=name,
        value=value,
        type=type,
        tags=tags,
        handler_name=handler_name,
    )


def report_event(
    name: str,
    level: EventLevel,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    handler_name: Optional[str] = None,
) -> None:
    """Report an event.

    Args:
        name: The name of the event
        level: The level of the event
        message: The message of the event
        data: Optional data for the event
        tags: Optional tags for the event
        handler_name: The name of the handler to use, or None for the default handler
    """
    manager = TelemetryManager.get_instance()
    manager.report_event(
        name=name,
        level=level,
        message=message,
        data=data,
        tags=tags,
        handler_name=handler_name,
    )


def enable_telemetry() -> None:
    """Enable telemetry."""
    manager = TelemetryManager.get_instance()
    manager.enable()


def disable_telemetry() -> None:
    """Disable telemetry."""
    manager = TelemetryManager.get_instance()
    manager.disable()


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled.

    Returns:
        True if telemetry is enabled, False otherwise
    """
    manager = TelemetryManager.get_instance()
    return manager.is_enabled()
