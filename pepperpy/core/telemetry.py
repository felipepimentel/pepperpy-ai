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

T = TypeVar("T")

logger = logging.getLogger(__name__)


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

    This class defines the interface for telemetry handlers, which are
    responsible for processing metrics and events reported by providers.
    """

    def handle_metric(self, metric: Metric) -> None:
        """Handle a metric reported by a provider.

        Args:
            metric: The metric to handle.
        """
        raise NotImplementedError("Subclasses must implement handle_metric")

    def handle_event(self, event: Event) -> None:
        """Handle an event reported by a provider.

        Args:
            event: The event to handle.
        """
        raise NotImplementedError("Subclasses must implement handle_event")


class LoggingTelemetryHandler(TelemetryHandler):
    """Telemetry handler that logs metrics and events.

    This handler logs metrics and events to the Python logging system.
    It's useful for development and debugging.
    """

    def handle_metric(self, metric: Metric) -> None:
        """Handle a metric by logging it.

        Args:
            metric: The metric to handle.
        """
        tags_str = " ".join(f"{k}={v}" for k, v in metric.tags.items())
        logger.info(
            "METRIC %s=%s type=%s %s",
            metric.name,
            metric.value,
            metric.type.value,
            tags_str,
        )

    def handle_event(self, event: Event) -> None:
        """Handle an event by logging it.

        Args:
            event: The event to handle.
        """
        log_level = getattr(logging, event.level.name)
        tags_str = " ".join(f"{k}={v}" for k, v in event.tags.items())
        logger.log(
            log_level,
            "EVENT %s: %s %s %s",
            event.name,
            event.message,
            tags_str,
            event.data,
        )


class CompositeTelemetryHandler(TelemetryHandler):
    """Telemetry handler that delegates to multiple handlers.

    This handler delegates to multiple handlers, allowing metrics and events
    to be processed by multiple systems simultaneously.
    """

    def __init__(self, handlers: List[TelemetryHandler]):
        """Initialize the composite handler.

        Args:
            handlers: The handlers to delegate to.
        """
        self.handlers = handlers

    def handle_metric(self, metric: Metric) -> None:
        """Handle a metric by delegating to all handlers.

        Args:
            metric: The metric to handle.
        """
        for handler in self.handlers:
            try:
                handler.handle_metric(metric)
            except Exception as e:
                logger.error("Error handling metric in %s: %s", handler, e)

    def handle_event(self, event: Event) -> None:
        """Handle an event by delegating to all handlers.

        Args:
            event: The event to handle.
        """
        for handler in self.handlers:
            try:
                handler.handle_event(event)
            except Exception as e:
                logger.error("Error handling event in %s: %s", handler, e)


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
            The singleton instance of the telemetry manager.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_handler(self, name: str, handler: TelemetryHandler) -> None:
        """Register a telemetry handler.

        Args:
            name: The name of the handler.
            handler: The handler to register.
        """
        self._handlers[name] = handler
        if self._default_handler is None:
            self._default_handler = handler

    def set_default_handler(self, name: str) -> None:
        """Set the default telemetry handler.

        Args:
            name: The name of the handler to set as default.

        Raises:
            KeyError: If the handler is not registered.
        """
        if name not in self._handlers:
            raise KeyError(f"Handler '{name}' is not registered")
        self._default_handler = self._handlers[name]

    def get_handler(self, name: Optional[str] = None) -> TelemetryHandler:
        """Get a telemetry handler.

        Args:
            name: The name of the handler to get. If None, the default handler is returned.

        Returns:
            The requested telemetry handler.

        Raises:
            KeyError: If the handler is not registered.
            ValueError: If no default handler is set.
        """
        if name is None:
            if self._default_handler is None:
                raise ValueError("No default handler is set")
            return self._default_handler
        if name not in self._handlers:
            raise KeyError(f"Handler '{name}' is not registered")
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
            name: The name of the metric.
            value: The value of the metric.
            type: The type of the metric.
            tags: Optional tags to associate with the metric.
            handler_name: Optional name of the handler to use.
        """
        if not self._enabled:
            return

        metric = Metric(
            name=name,
            value=value,
            type=type,
            tags=tags or {},
            timestamp=datetime.now(),
        )

        try:
            handler = self.get_handler(handler_name)
            handler.handle_metric(metric)
        except Exception as e:
            logger.error("Error reporting metric: %s", e)

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
            name: The name of the event.
            level: The level of the event.
            message: The message associated with the event.
            data: Optional data to associate with the event.
            tags: Optional tags to associate with the event.
            handler_name: Optional name of the handler to use.
        """
        if not self._enabled:
            return

        event = Event(
            name=name,
            level=level,
            message=message,
            data=data or {},
            tags=tags or {},
            timestamp=datetime.now(),
        )

        try:
            handler = self.get_handler(handler_name)
            handler.handle_event(event)
        except Exception as e:
            logger.error("Error reporting event: %s", e)

    def enable(self) -> None:
        """Enable telemetry reporting."""
        self._enabled = True

    def disable(self) -> None:
        """Disable telemetry reporting."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if telemetry reporting is enabled.

        Returns:
            True if telemetry reporting is enabled, False otherwise.
        """
        return self._enabled


class ProviderTelemetry:
    """Telemetry for a specific provider.

    This class provides telemetry methods for a specific provider,
    automatically tagging metrics and events with the provider ID.
    """

    def __init__(self, provider_id: str):
        """Initialize provider telemetry.

        Args:
            provider_id: The ID of the provider.
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
        """Report a metric for this provider.

        Args:
            name: The name of the metric.
            value: The value of the metric.
            type: The type of the metric.
            tags: Optional tags to associate with the metric.
            handler_name: Optional name of the handler to use.
        """
        all_tags = {"provider": self.provider_id}
        if tags:
            all_tags.update(tags)
        self.manager.report_metric(name, value, type, all_tags, handler_name)

    def report_event(
        self,
        name: str,
        level: EventLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report an event for this provider.

        Args:
            name: The name of the event.
            level: The level of the event.
            message: The message associated with the event.
            data: Optional data to associate with the event.
            tags: Optional tags to associate with the event.
            handler_name: Optional name of the handler to use.
        """
        all_tags = {"provider": self.provider_id}
        if tags:
            all_tags.update(tags)
        self.manager.report_event(name, level, message, data, all_tags, handler_name)

    def count(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a counter metric.

        Args:
            name: The name of the metric.
            value: The value to increment the counter by.
            tags: Optional tags to associate with the metric.
            handler_name: Optional name of the handler to use.
        """
        self.report_metric(name, value, MetricType.COUNTER, tags, handler_name)

    def gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a gauge metric.

        Args:
            name: The name of the metric.
            value: The current value of the gauge.
            tags: Optional tags to associate with the metric.
            handler_name: Optional name of the handler to use.
        """
        self.report_metric(name, value, MetricType.GAUGE, tags, handler_name)

    def histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> None:
        """Report a histogram metric.

        Args:
            name: The name of the metric.
            value: The value to add to the histogram.
            tags: Optional tags to associate with the metric.
            handler_name: Optional name of the handler to use.
        """
        self.report_metric(name, value, MetricType.HISTOGRAM, tags, handler_name)

    def time(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        handler_name: Optional[str] = None,
    ) -> "Timer":
        """Create a timer for measuring operation duration.

        Args:
            name: The name of the timer metric.
            tags: Optional tags to associate with the metric.
            handler_name: Optional name of the handler to use.

        Returns:
            A timer context manager.
        """
        return Timer(self, name, tags, handler_name)

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
            name: The name of the event.
            message: The message associated with the event.
            data: Optional data to associate with the event.
            tags: Optional tags to associate with the event.
            handler_name: Optional name of the handler to use.
        """
        self.report_event(name, EventLevel.DEBUG, message, data, tags, handler_name)

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
            name: The name of the event.
            message: The message associated with the event.
            data: Optional data to associate with the event.
            tags: Optional tags to associate with the event.
            handler_name: Optional name of the handler to use.
        """
        self.report_event(name, EventLevel.INFO, message, data, tags, handler_name)

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
            name: The name of the event.
            message: The message associated with the event.
            data: Optional data to associate with the event.
            tags: Optional tags to associate with the event.
            handler_name: Optional name of the handler to use.
        """
        self.report_event(name, EventLevel.WARNING, message, data, tags, handler_name)

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
            name: The name of the event.
            message: The message associated with the event.
            data: Optional data to associate with the event.
            tags: Optional tags to associate with the event.
            handler_name: Optional name of the handler to use.
        """
        self.report_event(name, EventLevel.ERROR, message, data, tags, handler_name)

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
            name: The name of the event.
            message: The message associated with the event.
            data: Optional data to associate with the event.
            tags: Optional tags to associate with the event.
            handler_name: Optional name of the handler to use.
        """
        self.report_event(name, EventLevel.CRITICAL, message, data, tags, handler_name)


class Timer:
    """Context manager for timing operations.

    This class provides a context manager for timing operations and
    reporting the duration as a timer metric.

    Example:
        ```python
        telemetry = ProviderTelemetry("openai")
        with telemetry.time("request_duration"):
            # Do something that takes time
            response = make_request()
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
            telemetry: The provider telemetry to report to.
            name: The name of the timer metric.
            tags: Optional tags to associate with the metric.
            handler_name: Optional name of the handler to use.
        """
        self.telemetry = telemetry
        self.name = name
        self.tags = tags
        self.handler_name = handler_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self) -> "Timer":
        """Start the timer.

        Returns:
            The timer instance.
        """
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the timer and report the duration.

        Args:
            exc_type: The exception type, if an exception was raised.
            exc_val: The exception value, if an exception was raised.
            exc_tb: The exception traceback, if an exception was raised.
        """
        self.end_time = time.time()
        if self.start_time is not None and self.end_time is not None:
            duration = self.end_time - self.start_time
            self.telemetry.report_metric(
                self.name,
                duration,
                MetricType.TIMER,
                self.tags,
                self.handler_name,
            )


# Initialize the default telemetry handler
def initialize_telemetry() -> None:
    """Initialize the telemetry system with default handlers."""
    manager = TelemetryManager.get_instance()
    manager.register_handler("logging", LoggingTelemetryHandler())
    manager.set_default_handler("logging")


# Initialize telemetry on module import
initialize_telemetry()


# Convenience functions


def get_provider_telemetry(provider_id: str) -> ProviderTelemetry:
    """Get telemetry for a specific provider.

    Args:
        provider_id: The ID of the provider.

    Returns:
        Telemetry for the specified provider.
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
        name: The name of the metric.
        value: The value of the metric.
        type: The type of the metric.
        tags: Optional tags to associate with the metric.
        handler_name: Optional name of the handler to use.
    """
    manager = TelemetryManager.get_instance()
    manager.report_metric(name, value, type, tags, handler_name)


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
        name: The name of the event.
        level: The level of the event.
        message: The message associated with the event.
        data: Optional data to associate with the event.
        tags: Optional tags to associate with the event.
        handler_name: Optional name of the handler to use.
    """
    manager = TelemetryManager.get_instance()
    manager.report_event(name, level, message, data, tags, handler_name)


def enable_telemetry() -> None:
    """Enable telemetry reporting."""
    manager = TelemetryManager.get_instance()
    manager.enable()


def disable_telemetry() -> None:
    """Disable telemetry reporting."""
    manager = TelemetryManager.get_instance()
    manager.disable()


def is_telemetry_enabled() -> bool:
    """Check if telemetry reporting is enabled.

    Returns:
        True if telemetry reporting is enabled, False otherwise.
    """
    manager = TelemetryManager.get_instance()
    return manager.is_enabled()
