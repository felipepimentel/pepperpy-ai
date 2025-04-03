"""Event system for PepperPy plugins.

This module provides an event system for plugins to communicate with each other
and with the PepperPy core. It uses a publish-subscribe model, where plugins can
publish events and subscribe to events from other plugins or the core.
"""

import asyncio
import enum
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
)

from pepperpy.core.errors import PluginError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type for event type
EventTypeVar = TypeVar("EventTypeVar", str, enum.Enum)


class EventPriority(enum.IntEnum):
    """Priority for event handlers."""

    # Highest priority, runs first
    HIGHEST = 0

    # High priority
    HIGH = 25

    # Normal priority (default)
    NORMAL = 50

    # Low priority
    LOW = 75

    # Lowest priority, runs last
    LOWEST = 100


@dataclass
class EventContext:
    """Context for an event."""

    # Unique ID for the event
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Timestamp when the event was created
    timestamp: float = field(default_factory=time.time)

    # Source of the event (plugin ID or "core")
    source: str = "core"

    # Whether the event has been canceled
    canceled: bool = False

    # Additional context data
    data: Dict[str, Any] = field(default_factory=dict)

    # Results from handlers
    results: Dict[str, Any] = field(default_factory=dict)

    def cancel(self) -> None:
        """Cancel the event."""
        self.canceled = True

    def add_result(self, plugin_id: str, result: Any) -> None:
        """Add a result from a handler.

        Args:
            plugin_id: ID of the plugin that handled the event
            result: Result from the handler
        """
        self.results[plugin_id] = result

    def get_result(self, plugin_id: str) -> Optional[Any]:
        """Get a result from a handler.

        Args:
            plugin_id: ID of the plugin that handled the event

        Returns:
            Result from the handler, or None if not found
        """
        return self.results.get(plugin_id)

    def get_all_results(self) -> Dict[str, Any]:
        """Get all results from handlers.

        Returns:
            Dictionary of plugin IDs to results
        """
        return self.results.copy()

    def __str__(self) -> str:
        """Get string representation of the event context.

        Returns:
            String representation
        """
        return f"EventContext(id={self.event_id}, source={self.source}, canceled={self.canceled})"


class EventError(PluginError):
    """Error raised during event processing."""

    pass


@dataclass
class EventHandlerData:
    """Data for an event handler."""

    # Handler function
    handler: Union[
        Callable[[str, EventContext, Any], Any],
        Callable[[str, EventContext, Any], asyncio.Future],
    ]

    # Plugin ID
    plugin_id: str

    # Priority
    priority: EventPriority = EventPriority.NORMAL

    # Whether the handler is async
    is_async: bool = False

    # Whether to call the handler even if the event is canceled
    call_if_canceled: bool = False


class EventBus:
    """Event bus for PepperPy plugins.

    This class provides a central event bus for plugins to publish and subscribe
    to events. It supports both synchronous and asynchronous event handlers.
    """

    def __init__(self):
        """Initialize the event bus."""
        # Event handlers by event type
        self._handlers: Dict[str, List[EventHandlerData]] = {}

        # Lock for thread safety
        self._lock = threading.RLock()

        # Event hooks
        self._pre_dispatch_hooks: List[Callable[[str, EventContext, Any], None]] = []
        self._post_dispatch_hooks: List[Callable[[str, EventContext, Any], None]] = []

    def subscribe(
        self,
        event_type: Union[str, enum.Enum],
        handler: Union[
            Callable[[str, EventContext, Any], Any],
            Callable[[str, EventContext, Any], asyncio.Future],
        ],
        plugin_id: str,
        priority: EventPriority = EventPriority.NORMAL,
        call_if_canceled: bool = False,
    ) -> None:
        """Subscribe to an event.

        Args:
            event_type: Type of event to subscribe to
            handler: Event handler function
            plugin_id: ID of the plugin subscribing
            priority: Priority for the handler
            call_if_canceled: Whether to call the handler even if the event is canceled
        """
        # Convert enum to string
        event_type_str = (
            event_type.value if isinstance(event_type, enum.Enum) else event_type
        )

        # Check if handler is async
        is_async = asyncio.iscoroutinefunction(handler)

        with self._lock:
            # Initialize handlers list if needed
            if event_type_str not in self._handlers:
                self._handlers[event_type_str] = []

            # Create handler data
            handler_data = EventHandlerData(
                handler=handler,
                plugin_id=plugin_id,
                priority=priority,
                is_async=is_async,
                call_if_canceled=call_if_canceled,
            )

            # Add handler
            self._handlers[event_type_str].append(handler_data)

            # Sort handlers by priority
            self._handlers[event_type_str].sort(key=lambda h: h.priority)

        logger.debug(
            f"Subscribed to event {event_type_str}: {plugin_id} (priority={priority.name})"
        )

    def unsubscribe(
        self, event_type: Union[str, enum.Enum], handler: Callable, plugin_id: str
    ) -> bool:
        """Unsubscribe from an event.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Event handler function
            plugin_id: ID of the plugin unsubscribing

        Returns:
            True if the handler was unsubscribed, False otherwise
        """
        # Convert enum to string
        event_type_str = (
            event_type.value if isinstance(event_type, enum.Enum) else event_type
        )

        with self._lock:
            # Check if event type exists
            if event_type_str not in self._handlers:
                return False

            # Find handler
            for i, handler_data in enumerate(self._handlers[event_type_str]):
                if (
                    handler_data.handler == handler
                    and handler_data.plugin_id == plugin_id
                ):
                    # Remove handler
                    self._handlers[event_type_str].pop(i)
                    logger.debug(
                        f"Unsubscribed from event {event_type_str}: {plugin_id}"
                    )
                    return True

            return False

    def unsubscribe_all(self, plugin_id: str) -> int:
        """Unsubscribe from all events.

        Args:
            plugin_id: ID of the plugin unsubscribing

        Returns:
            Number of handlers unsubscribed
        """
        count = 0

        with self._lock:
            # Unsubscribe from all event types
            for event_type in list(self._handlers.keys()):
                # Find handlers for this plugin
                handlers = self._handlers[event_type]
                self._handlers[event_type] = [
                    h for h in handlers if h.plugin_id != plugin_id
                ]

                # Count unsubscribed handlers
                count += len(handlers) - len(self._handlers[event_type])

        logger.debug(f"Unsubscribed from all events: {plugin_id} ({count} handlers)")
        return count

    def publish(
        self,
        event_type: Union[str, enum.Enum],
        source: str,
        data: Any = None,
        context: Optional[EventContext] = None,
    ) -> EventContext:
        """Publish an event.

        Args:
            event_type: Type of event to publish
            source: Source of the event (plugin ID or "core")
            data: Event data
            context: Optional event context

        Returns:
            Event context with results
        """
        # Convert enum to string
        event_type_str = (
            event_type.value if isinstance(event_type, enum.Enum) else event_type
        )

        # Create context if not provided
        if context is None:
            context = EventContext(source=source)

        # Call pre-dispatch hooks
        self._call_pre_dispatch_hooks(event_type_str, context, data)

        with self._lock:
            # Check if event type has handlers
            if event_type_str not in self._handlers:
                logger.debug(f"No handlers for event {event_type_str}")
                return context

            # Get handlers
            handlers = self._handlers[event_type_str].copy()

        # Call handlers
        for handler_data in handlers:
            # Skip if event is canceled and handler doesn't want canceled events
            if context.canceled and not handler_data.call_if_canceled:
                continue

            try:
                # Call handler
                result = handler_data.handler(event_type_str, context, data)

                # Store result
                context.add_result(handler_data.plugin_id, result)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event_type_str} ({handler_data.plugin_id}): {e}",
                    exc_info=True,
                )

        # Call post-dispatch hooks
        self._call_post_dispatch_hooks(event_type_str, context, data)

        return context

    async def publish_async(
        self,
        event_type: Union[str, enum.Enum],
        source: str,
        data: Any = None,
        context: Optional[EventContext] = None,
    ) -> EventContext:
        """Publish an event asynchronously.

        Args:
            event_type: Type of event to publish
            source: Source of the event (plugin ID or "core")
            data: Event data
            context: Optional event context

        Returns:
            Event context with results
        """
        # Convert enum to string
        event_type_str = (
            event_type.value if isinstance(event_type, enum.Enum) else event_type
        )

        # Create context if not provided
        if context is None:
            context = EventContext(source=source)

        # Call pre-dispatch hooks
        self._call_pre_dispatch_hooks(event_type_str, context, data)

        with self._lock:
            # Check if event type has handlers
            if event_type_str not in self._handlers:
                logger.debug(f"No handlers for event {event_type_str}")
                return context

            # Get handlers
            handlers = self._handlers[event_type_str].copy()

        # Call handlers
        for handler_data in handlers:
            # Skip if event is canceled and handler doesn't want canceled events
            if context.canceled and not handler_data.call_if_canceled:
                continue

            try:
                # Call handler (sync or async)
                if handler_data.is_async:
                    # Call async handler
                    result = await handler_data.handler(event_type_str, context, data)
                else:
                    # Call sync handler
                    result = handler_data.handler(event_type_str, context, data)

                # Store result
                context.add_result(handler_data.plugin_id, result)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event_type_str} ({handler_data.plugin_id}): {e}",
                    exc_info=True,
                )

        # Call post-dispatch hooks
        self._call_post_dispatch_hooks(event_type_str, context, data)

        return context

    def has_handlers(self, event_type: Union[str, enum.Enum]) -> bool:
        """Check if an event type has handlers.

        Args:
            event_type: Type of event to check

        Returns:
            True if the event type has handlers, False otherwise
        """
        # Convert enum to string
        event_type_str = (
            event_type.value if isinstance(event_type, enum.Enum) else event_type
        )

        with self._lock:
            return (
                event_type_str in self._handlers
                and len(self._handlers[event_type_str]) > 0
            )

    def get_handler_count(self, event_type: Union[str, enum.Enum]) -> int:
        """Get the number of handlers for an event type.

        Args:
            event_type: Type of event to check

        Returns:
            Number of handlers
        """
        # Convert enum to string
        event_type_str = (
            event_type.value if isinstance(event_type, enum.Enum) else event_type
        )

        with self._lock:
            if event_type_str not in self._handlers:
                return 0

            return len(self._handlers[event_type_str])

    def get_subscribed_events(self, plugin_id: str) -> List[str]:
        """Get the event types that a plugin is subscribed to.

        Args:
            plugin_id: ID of the plugin

        Returns:
            List of event types
        """
        result = []

        with self._lock:
            for event_type, handlers in self._handlers.items():
                for handler in handlers:
                    if handler.plugin_id == plugin_id:
                        result.append(event_type)
                        break

        return result

    def add_pre_dispatch_hook(
        self, hook: Callable[[str, EventContext, Any], None]
    ) -> None:
        """Add a pre-dispatch hook.

        Pre-dispatch hooks are called before dispatching an event to handlers.

        Args:
            hook: Pre-dispatch hook function
        """
        with self._lock:
            self._pre_dispatch_hooks.append(hook)

    def add_post_dispatch_hook(
        self, hook: Callable[[str, EventContext, Any], None]
    ) -> None:
        """Add a post-dispatch hook.

        Post-dispatch hooks are called after dispatching an event to handlers.

        Args:
            hook: Post-dispatch hook function
        """
        with self._lock:
            self._post_dispatch_hooks.append(hook)

    def remove_pre_dispatch_hook(
        self, hook: Callable[[str, EventContext, Any], None]
    ) -> bool:
        """Remove a pre-dispatch hook.

        Args:
            hook: Pre-dispatch hook function

        Returns:
            True if the hook was removed, False otherwise
        """
        with self._lock:
            if hook in self._pre_dispatch_hooks:
                self._pre_dispatch_hooks.remove(hook)
                return True

            return False

    def remove_post_dispatch_hook(
        self, hook: Callable[[str, EventContext, Any], None]
    ) -> bool:
        """Remove a post-dispatch hook.

        Args:
            hook: Post-dispatch hook function

        Returns:
            True if the hook was removed, False otherwise
        """
        with self._lock:
            if hook in self._post_dispatch_hooks:
                self._post_dispatch_hooks.remove(hook)
                return True

            return False

    def _call_pre_dispatch_hooks(
        self, event_type: str, context: EventContext, data: Any
    ) -> None:
        """Call pre-dispatch hooks.

        Args:
            event_type: Type of event
            context: Event context
            data: Event data
        """
        for hook in self._pre_dispatch_hooks:
            try:
                hook(event_type, context, data)
            except Exception as e:
                logger.error(f"Error in pre-dispatch hook: {e}", exc_info=True)

    def _call_post_dispatch_hooks(
        self, event_type: str, context: EventContext, data: Any
    ) -> None:
        """Call post-dispatch hooks.

        Args:
            event_type: Type of event
            context: Event context
            data: Event data
        """
        for hook in self._post_dispatch_hooks:
            try:
                hook(event_type, context, data)
            except Exception as e:
                logger.error(f"Error in post-dispatch hook: {e}", exc_info=True)


# Singleton instance
_event_bus = EventBus()


# Common events
class CoreEventType(enum.Enum):
    """Core event types."""

    # Plugin lifecycle events
    PLUGIN_REGISTERED = "core.plugin.registered"
    PLUGIN_UNREGISTERED = "core.plugin.unregistered"
    PLUGIN_INITIALIZING = "core.plugin.initializing"
    PLUGIN_INITIALIZED = "core.plugin.initialized"
    PLUGIN_INITIALIZATION_FAILED = "core.plugin.initialization_failed"
    PLUGIN_CLEANUP_STARTED = "core.plugin.cleanup_started"
    PLUGIN_CLEANUP_COMPLETED = "core.plugin.cleanup_completed"
    PLUGIN_CLEANUP_FAILED = "core.plugin.cleanup_failed"

    # System lifecycle events
    SYSTEM_STARTUP = "core.system.startup"
    SYSTEM_SHUTDOWN = "core.system.shutdown"

    # Configuration events
    CONFIG_CHANGED = "core.config.changed"

    # Resource events
    RESOURCE_REGISTERED = "core.resource.registered"
    RESOURCE_UNREGISTERED = "core.resource.unregistered"
    RESOURCE_CLEANUP_STARTED = "core.resource.cleanup_started"
    RESOURCE_CLEANUP_COMPLETED = "core.resource.cleanup_completed"
    RESOURCE_CLEANUP_FAILED = "core.resource.cleanup_failed"


# Public API
def subscribe(
    event_type: Union[str, enum.Enum],
    handler: Union[
        Callable[[str, EventContext, Any], Any],
        Callable[[str, EventContext, Any], asyncio.Future],
    ],
    plugin_id: str,
    priority: EventPriority = EventPriority.NORMAL,
    call_if_canceled: bool = False,
) -> None:
    """Subscribe to an event.

    Args:
        event_type: Type of event to subscribe to
        handler: Event handler function
        plugin_id: ID of the plugin subscribing
        priority: Priority for the handler
        call_if_canceled: Whether to call the handler even if the event is canceled
    """
    _event_bus.subscribe(
        event_type=event_type,
        handler=handler,
        plugin_id=plugin_id,
        priority=priority,
        call_if_canceled=call_if_canceled,
    )


def unsubscribe(
    event_type: Union[str, enum.Enum], handler: Callable, plugin_id: str
) -> bool:
    """Unsubscribe from an event.

    Args:
        event_type: Type of event to unsubscribe from
        handler: Event handler function
        plugin_id: ID of the plugin unsubscribing

    Returns:
        True if the handler was unsubscribed, False otherwise
    """
    return _event_bus.unsubscribe(
        event_type=event_type, handler=handler, plugin_id=plugin_id
    )


def unsubscribe_all(plugin_id: str) -> int:
    """Unsubscribe from all events.

    Args:
        plugin_id: ID of the plugin unsubscribing

    Returns:
        Number of handlers unsubscribed
    """
    return _event_bus.unsubscribe_all(plugin_id=plugin_id)


def publish(
    event_type: Union[str, enum.Enum],
    source: str,
    data: Any = None,
    context: Optional[EventContext] = None,
) -> EventContext:
    """Publish an event.

    Args:
        event_type: Type of event to publish
        source: Source of the event (plugin ID or "core")
        data: Event data
        context: Optional event context

    Returns:
        Event context with results
    """
    return _event_bus.publish(
        event_type=event_type, source=source, data=data, context=context
    )


async def publish_async(
    event_type: Union[str, enum.Enum],
    source: str,
    data: Any = None,
    context: Optional[EventContext] = None,
) -> EventContext:
    """Publish an event asynchronously.

    Args:
        event_type: Type of event to publish
        source: Source of the event (plugin ID or "core")
        data: Event data
        context: Optional event context

    Returns:
        Event context with results
    """
    return await _event_bus.publish_async(
        event_type=event_type, source=source, data=data, context=context
    )


def has_handlers(event_type: Union[str, enum.Enum]) -> bool:
    """Check if an event type has handlers.

    Args:
        event_type: Type of event to check

    Returns:
        True if the event type has handlers, False otherwise
    """
    return _event_bus.has_handlers(event_type=event_type)


def get_handler_count(event_type: Union[str, enum.Enum]) -> int:
    """Get the number of handlers for an event type.

    Args:
        event_type: Type of event to check

    Returns:
        Number of handlers
    """
    return _event_bus.get_handler_count(event_type=event_type)


def get_subscribed_events(plugin_id: str) -> List[str]:
    """Get the event types that a plugin is subscribed to.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of event types
    """
    return _event_bus.get_subscribed_events(plugin_id=plugin_id)


def add_pre_dispatch_hook(hook: Callable[[str, EventContext, Any], None]) -> None:
    """Add a pre-dispatch hook.

    Pre-dispatch hooks are called before dispatching an event to handlers.

    Args:
        hook: Pre-dispatch hook function
    """
    _event_bus.add_pre_dispatch_hook(hook=hook)


def add_post_dispatch_hook(hook: Callable[[str, EventContext, Any], None]) -> None:
    """Add a post-dispatch hook.

    Post-dispatch hooks are called after dispatching an event to handlers.

    Args:
        hook: Post-dispatch hook function
    """
    _event_bus.add_post_dispatch_hook(hook=hook)


def remove_pre_dispatch_hook(hook: Callable[[str, EventContext, Any], None]) -> bool:
    """Remove a pre-dispatch hook.

    Args:
        hook: Pre-dispatch hook function

    Returns:
        True if the hook was removed, False otherwise
    """
    return _event_bus.remove_pre_dispatch_hook(hook=hook)


def remove_post_dispatch_hook(hook: Callable[[str, EventContext, Any], None]) -> bool:
    """Remove a post-dispatch hook.

    Args:
        hook: Post-dispatch hook function

    Returns:
        True if the hook was removed, False otherwise
    """
    return _event_bus.remove_post_dispatch_hook(hook=hook)


def get_event_bus() -> EventBus:
    """Get the event bus instance.

    Returns:
        Event bus instance
    """
    return _event_bus


class EventEmitter:
    """Mixin class for plugins to emit events.

    This class provides convenience methods for plugins to emit events
    and handle their own plugin ID.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the event emitter.

        This method should be called from the plugin's __init__ method.
        """
        # Set plugin ID if not set by child class
        if not hasattr(self, "plugin_id"):
            self.plugin_id = self.__class__.__name__

        super().__init__(*args, **kwargs)

    def emit_event(
        self,
        event_type: Union[str, enum.Enum],
        data: Any = None,
        context: Optional[EventContext] = None,
    ) -> EventContext:
        """Emit an event.

        Args:
            event_type: Type of event to emit
            data: Event data
            context: Optional event context

        Returns:
            Event context with results
        """
        return publish(
            event_type=event_type,
            source=self.plugin_id,
            data=data,
            context=context,
        )

    async def emit_event_async(
        self,
        event_type: Union[str, enum.Enum],
        data: Any = None,
        context: Optional[EventContext] = None,
    ) -> EventContext:
        """Emit an event asynchronously.

        Args:
            event_type: Type of event to emit
            data: Event data
            context: Optional event context

        Returns:
            Event context with results
        """
        return await publish_async(
            event_type=event_type,
            source=self.plugin_id,
            data=data,
            context=context,
        )

    def subscribe_to_event(
        self,
        event_type: Union[str, enum.Enum],
        handler: Union[
            Callable[[str, EventContext, Any], Any],
            Callable[[str, EventContext, Any], asyncio.Future],
        ],
        priority: EventPriority = EventPriority.NORMAL,
        call_if_canceled: bool = False,
    ) -> None:
        """Subscribe to an event.

        Args:
            event_type: Type of event to subscribe to
            handler: Event handler function
            priority: Priority for the handler
            call_if_canceled: Whether to call the handler even if the event is canceled
        """
        subscribe(
            event_type=event_type,
            handler=handler,
            plugin_id=self.plugin_id,
            priority=priority,
            call_if_canceled=call_if_canceled,
        )

    def unsubscribe_from_event(
        self, event_type: Union[str, enum.Enum], handler: Callable
    ) -> bool:
        """Unsubscribe from an event.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Event handler function

        Returns:
            True if the handler was unsubscribed, False otherwise
        """
        return unsubscribe(
            event_type=event_type, handler=handler, plugin_id=self.plugin_id
        )

    def unsubscribe_from_all_events(self) -> int:
        """Unsubscribe from all events.

        Returns:
            Number of handlers unsubscribed
        """
        return unsubscribe_all(plugin_id=self.plugin_id)

    def get_subscribed_events(self) -> List[str]:
        """Get the event types that this plugin is subscribed to.

        Returns:
            List of event types
        """
        return get_subscribed_events(plugin_id=self.plugin_id)
