"""Event system for PepperPy.

This module provides a simple event-based system for PepperPy components to communicate with each other.
The event system uses a publish-subscribe pattern where components can subscribe to specific event types
and be notified when those events occur.

Example:
    ```python
    from pepperpy.infra.events import EventBus, Event

    # Define a custom event
    class MyEvent(Event):
        def __init__(self, source, data):
            super().__init__(source)
            self.data = data

    # Create an event handler
    def handle_my_event(event):
        print(f"Event received from {event.source}: {event.data}")

    # Subscribe to the event
    EventBus.subscribe(MyEvent, handle_my_event)

    # Publish an event
    EventBus.publish(MyEvent("my_component", "Hello World"))
    ```
"""

from __future__ import annotations

import inspect
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar

from pepperpy.core.errors import PepperPyError

# Type definitions
EventType = TypeVar("EventType", bound="Event")
EventHandler = Callable[[EventType], None]
EventFilter = Callable[[EventType], bool]

# Configure logging
logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Priority levels for event handlers."""

    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class Event:
    """Base class for all events in the system."""

    def __init__(self, source: str):
        """Initialize a new event.

        Args:
            source: The source of the event (component or service name)
        """
        self.id = str(uuid.uuid4())
        self.source = source
        self.timestamp = datetime.now()
        self.metadata: Dict[str, Any] = {}

    def __str__(self) -> str:
        """Get a string representation of the event.

        Returns:
            A string representing the event
        """
        return f"{self.__class__.__name__}(id={self.id}, source={self.source}, timestamp={self.timestamp})"


class SystemEvent(Event):
    """Base class for system-level events."""

    pass


class StartupEvent(SystemEvent):
    """Event fired when the system starts up."""

    pass


class ShutdownEvent(SystemEvent):
    """Event fired when the system is shutting down."""

    pass


class ComponentInitializedEvent(SystemEvent):
    """Event fired when a component is initialized."""

    def __init__(self, source: str, component_name: str):
        """Initialize a new component initialized event.

        Args:
            source: The source of the event
            component_name: The name of the component that was initialized
        """
        super().__init__(source)
        self.component_name = component_name


class ErrorEvent(SystemEvent):
    """Event fired when an error occurs."""

    def __init__(
        self, source: str, error: Exception, context: Optional[Dict[str, Any]] = None
    ):
        """Initialize a new error event.

        Args:
            source: The source of the event
            error: The error that occurred
            context: Additional context information about the error
        """
        super().__init__(source)
        self.error = error
        self.context = context or {}


@dataclass
class Subscription:
    """A subscription to an event type."""

    event_type: Type[Event]
    handler: EventHandler
    priority: EventPriority = EventPriority.NORMAL
    filter_func: Optional[EventFilter] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class EventBusError(PepperPyError):
    """Error raised when there is an issue with the event bus."""

    pass


class EventBus:
    """Central event bus for the PepperPy framework."""

    _subscriptions: Dict[Type[Event], List[Subscription]] = {}
    _global_subscriptions: List[Subscription] = []
    _lock = threading.RLock()
    _enabled = True

    @classmethod
    def subscribe(
        cls,
        event_type: Type[EventType],
        handler: EventHandler,
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[EventFilter] = None,
    ) -> str:
        """Subscribe to events of a specific type.

        Args:
            event_type: The type of event to subscribe to
            handler: The function to call when the event occurs
            priority: The priority of the subscription
            filter_func: Optional function to filter events

        Returns:
            The subscription ID
        """
        with cls._lock:
            subscription = Subscription(event_type, handler, priority, filter_func)
            if event_type == Event:
                cls._global_subscriptions.append(subscription)
                cls._global_subscriptions.sort(
                    key=lambda s: s.priority.value, reverse=True
                )
            else:
                if event_type not in cls._subscriptions:
                    cls._subscriptions[event_type] = []
                cls._subscriptions[event_type].append(subscription)
                cls._subscriptions[event_type].sort(
                    key=lambda s: s.priority.value, reverse=True
                )
            return subscription.id

    @classmethod
    def unsubscribe(cls, subscription_id: str) -> bool:
        """Unsubscribe from events using the subscription ID.

        Args:
            subscription_id: The ID of the subscription to remove

        Returns:
            True if the subscription was removed, False otherwise
        """
        with cls._lock:
            # Check global subscriptions
            for i, subscription in enumerate(cls._global_subscriptions):
                if subscription.id == subscription_id:
                    cls._global_subscriptions.pop(i)
                    return True

            # Check type-specific subscriptions
            for event_type, subscriptions in cls._subscriptions.items():
                for i, subscription in enumerate(subscriptions):
                    if subscription.id == subscription_id:
                        subscriptions.pop(i)
                        if not subscriptions:
                            del cls._subscriptions[event_type]
                        return True

            return False

    @classmethod
    def publish(cls, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The event to publish
        """
        if not cls._enabled:
            return

        event_type = type(event)
        handled = False

        # Call handlers in priority order
        with cls._lock:
            # Call type-specific handlers
            for base_class in inspect.getmro(event_type):
                if base_class == object:
                    continue

                if base_class in cls._subscriptions:
                    for subscription in cls._subscriptions[base_class]:
                        if subscription.filter_func and not subscription.filter_func(
                            event
                        ):
                            continue
                        try:
                            subscription.handler(event)
                            handled = True
                        except Exception as e:
                            logger.exception(f"Error in event handler: {e}")

            # Call global handlers
            for subscription in cls._global_subscriptions:
                if subscription.filter_func and not subscription.filter_func(event):
                    continue
                try:
                    subscription.handler(event)
                    handled = True
                except Exception as e:
                    logger.exception(f"Error in global event handler: {e}")

        if not handled:
            logger.debug(f"No handlers for event: {event}")

    @classmethod
    def clear_all_subscriptions(cls) -> None:
        """Clear all subscriptions from the event bus."""
        with cls._lock:
            cls._subscriptions.clear()
            cls._global_subscriptions.clear()

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if the event bus is enabled.

        Returns:
            True if the event bus is enabled, False otherwise
        """
        return cls._enabled

    @classmethod
    def enable(cls) -> None:
        """Enable the event bus."""
        cls._enabled = True

    @classmethod
    def disable(cls) -> None:
        """Disable the event bus."""
        cls._enabled = False


# Common application events


class LogEvent(Event):
    """Event fired when a log message is generated."""

    def __init__(self, source: str, level: int, message: str):
        """Initialize a new log event.

        Args:
            source: The source of the event
            level: The log level (using logging module levels)
            message: The log message
        """
        super().__init__(source)
        self.level = level
        self.message = message


class ConfigChangedEvent(Event):
    """Event fired when configuration changes."""

    def __init__(self, source: str, key: str, old_value: Any, new_value: Any):
        """Initialize a new config changed event.

        Args:
            source: The source of the event
            key: The configuration key that changed
            old_value: The old value
            new_value: The new value
        """
        super().__init__(source)
        self.key = key
        self.old_value = old_value
        self.new_value = new_value


class ResourceEvent(Event):
    """Base class for resource-related events."""

    def __init__(self, source: str, resource_type: str, resource_id: str):
        """Initialize a new resource event.

        Args:
            source: The source of the event
            resource_type: The type of resource
            resource_id: The ID of the resource
        """
        super().__init__(source)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceCreatedEvent(ResourceEvent):
    """Event fired when a resource is created."""

    pass


class ResourceUpdatedEvent(ResourceEvent):
    """Event fired when a resource is updated."""

    pass


class ResourceDeletedEvent(ResourceEvent):
    """Event fired when a resource is deleted."""

    pass


# Performance monitoring events


class PerformanceEvent(Event):
    """Base class for performance-related events."""

    def __init__(self, source: str, operation: str, duration_ms: float):
        """Initialize a new performance event.

        Args:
            source: The source of the event
            operation: The operation being measured
            duration_ms: The duration of the operation in milliseconds
        """
        super().__init__(source)
        self.operation = operation
        self.duration_ms = duration_ms


class SlowOperationEvent(PerformanceEvent):
    """Event fired when an operation takes longer than expected."""

    def __init__(
        self, source: str, operation: str, duration_ms: float, threshold_ms: float
    ):
        """Initialize a new slow operation event.

        Args:
            source: The source of the event
            operation: The operation being measured
            duration_ms: The duration of the operation in milliseconds
            threshold_ms: The threshold that was exceeded
        """
        super().__init__(source, operation, duration_ms)
        self.threshold_ms = threshold_ms


# Event decorators and utilities


def event_handler(
    event_type: Type[EventType], priority: EventPriority = EventPriority.NORMAL
):
    """Decorator to register a function as an event handler.

    Args:
        event_type: The type of event to handle
        priority: The priority of the handler

    Returns:
        The decorated function
    """

    def decorator(func):
        EventBus.subscribe(event_type, func, priority)
        return func

    return decorator


class EventRecorder:
    """Utility class for recording events for testing or debugging."""

    def __init__(self, event_types: Optional[Set[Type[Event]]] = None):
        """Initialize a new event recorder.

        Args:
            event_types: Optional set of event types to record
        """
        self.events: List[Event] = []
        self.event_types = event_types
        self.subscription_ids: List[str] = []

    def __enter__(self):
        """Start recording events.

        Returns:
            This recorder instance
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop recording events."""
        self.stop()

    def start(self):
        """Start recording events."""
        if self.event_types:
            for event_type in self.event_types:
                sub_id = EventBus.subscribe(event_type, self._record_event)
                self.subscription_ids.append(sub_id)
        else:
            sub_id = EventBus.subscribe(Event, self._record_event)
            self.subscription_ids.append(sub_id)

    def stop(self):
        """Stop recording events."""
        for sub_id in self.subscription_ids:
            EventBus.unsubscribe(sub_id)
        self.subscription_ids.clear()

    def _record_event(self, event: Event):
        """Record an event.

        Args:
            event: The event to record
        """
        self.events.append(event)

    def clear(self):
        """Clear all recorded events."""
        self.events.clear()

    def get_events_by_type(self, event_type: Type[Event]) -> List[Event]:
        """Get all recorded events of a specific type.

        Args:
            event_type: The event type to filter by

        Returns:
            A list of events of the specified type
        """
        return [e for e in self.events if isinstance(e, event_type)]


# Performance monitoring decorator
def track_performance(
    threshold_ms: Optional[float] = None, event_source: Optional[str] = None
):
    """Decorator to track the performance of a function.

    Args:
        threshold_ms: Optional threshold in milliseconds for slow operation events
        event_source: Optional source name for events

    Returns:
        The decorated function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            source = event_source or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start_time) * 1000
                event = PerformanceEvent(source, func.__name__, duration_ms)
                EventBus.publish(event)

                if threshold_ms is not None and duration_ms > threshold_ms:
                    slow_event = SlowOperationEvent(
                        source, func.__name__, duration_ms, threshold_ms
                    )
                    EventBus.publish(slow_event)

        return wrapper

    return decorator
