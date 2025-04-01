"""Event system for PepperPy.

This module provides an event-driven architecture for PepperPy, allowing
components to communicate without direct coupling through events.
"""

import asyncio
import enum
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, TypeVar, Union, cast

from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger

T = TypeVar("T")
EventHandlerType = Callable[[Dict[str, Any]], Awaitable[None]]
SyncEventHandlerType = Callable[[Dict[str, Any]], None]


class EventError(PepperpyError):
    """Error related to events."""
    
    def __init__(
        self,
        message: str,
        event_type: Optional[str] = None,
        handler: Optional[str] = None,
        *args,
        **kwargs
    ):
        """Initialize event error.
        
        Args:
            message: Error message
            event_type: Optional event type
            handler: Optional handler name
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.event_type = event_type
        self.handler = handler


class EventType(str, enum.Enum):
    """Standard event types for PepperPy."""
    
    # Lifecycle events
    INITIALIZE = "pepperpy.initialize"
    CONFIGURED = "pepperpy.configured"
    SHUTDOWN = "pepperpy.shutdown"
    
    # Processing events
    PROCESS_START = "pepperpy.process.start"
    PROCESS_COMPLETE = "pepperpy.process.complete"
    PROCESS_ERROR = "pepperpy.process.error"
    
    # LLM events
    LLM_REQUEST = "pepperpy.llm.request"
    LLM_RESPONSE = "pepperpy.llm.response"
    LLM_ERROR = "pepperpy.llm.error"
    
    # RAG events
    RAG_QUERY = "pepperpy.rag.query"
    RAG_RESULTS = "pepperpy.rag.results"
    RAG_ERROR = "pepperpy.rag.error"
    
    # Document events
    DOCUMENT_CREATED = "pepperpy.document.created"
    DOCUMENT_UPDATED = "pepperpy.document.updated"
    DOCUMENT_DELETED = "pepperpy.document.deleted"
    
    # Plugin events
    PLUGIN_LOADED = "pepperpy.plugin.loaded"
    PLUGIN_INITIALIZED = "pepperpy.plugin.initialized"
    PLUGIN_ERROR = "pepperpy.plugin.error"
    
    # Workflow events
    WORKFLOW_START = "pepperpy.workflow.start"
    WORKFLOW_STEP_START = "pepperpy.workflow.step.start"
    WORKFLOW_STEP_COMPLETE = "pepperpy.workflow.step.complete"
    WORKFLOW_COMPLETE = "pepperpy.workflow.complete"
    WORKFLOW_ERROR = "pepperpy.workflow.error"


@dataclass
class Event:
    """Event data structure."""
    
    type: str
    data: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data
        }


class EventBus:
    """Event bus for PepperPy.
    
    The event bus allows components to publish events and subscribe to them,
    enabling loose coupling between components.
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self._handlers: Dict[str, List[EventHandlerType]] = {}
        self._wildcard_handlers: List[EventHandlerType] = []
        self._lock = threading.RLock()
        self._logger = get_logger("pepperpy.events")
        
    def subscribe(
        self,
        event_type: Union[str, EventType],
        handler: Union[EventHandlerType, SyncEventHandlerType]
    ) -> None:
        """Subscribe to an event.
        
        Args:
            event_type: Type of event to subscribe to, or "*" for all events
            handler: Event handler function
        """
        event_type_str = str(event_type)
        
        # Ensure handler is async
        async_handler = self._ensure_async_handler(handler)
        
        with self._lock:
            if event_type_str == "*":
                self._wildcard_handlers.append(async_handler)
                self._logger.debug(f"Registered wildcard handler: {handler.__name__}")
            else:
                if event_type_str not in self._handlers:
                    self._handlers[event_type_str] = []
                    
                self._handlers[event_type_str].append(async_handler)
                self._logger.debug(f"Registered handler for {event_type_str}: {handler.__name__}")
                
    def unsubscribe(
        self,
        event_type: Union[str, EventType],
        handler: Union[EventHandlerType, SyncEventHandlerType]
    ) -> None:
        """Unsubscribe from an event.
        
        Args:
            event_type: Type of event to unsubscribe from, or "*" for all events
            handler: Event handler function
        """
        event_type_str = str(event_type)
        
        # Get handler function (needed for comparison)
        if asyncio.iscoroutinefunction(handler):
            func = handler
        else:
            # For wrapped handlers, we need to get the original function
            if hasattr(handler, "__wrapped__"):
                func = getattr(handler, "__wrapped__")
            else:
                func = handler
                
        with self._lock:
            if event_type_str == "*":
                self._wildcard_handlers = [
                    h for h in self._wildcard_handlers
                    if not self._is_same_handler(h, func)
                ]
                self._logger.debug(f"Unregistered wildcard handler: {func.__name__}")
            elif event_type_str in self._handlers:
                self._handlers[event_type_str] = [
                    h for h in self._handlers[event_type_str]
                    if not self._is_same_handler(h, func)
                ]
                self._logger.debug(f"Unregistered handler for {event_type_str}: {func.__name__}")
                
    def _is_same_handler(self, h1: EventHandlerType, h2: Callable) -> bool:
        """Check if two handlers are the same.
        
        Args:
            h1: First handler
            h2: Second handler
            
        Returns:
            True if handlers are the same, False otherwise
        """
        # Check if it's a direct match
        if h1 == h2:
            return True
            
        # Check if it's a wrapped function
        if hasattr(h1, "__wrapped__"):
            return self._is_same_handler(getattr(h1, "__wrapped__"), h2)
            
        return False
                
    async def publish(
        self,
        event_type: Union[str, EventType],
        data: Dict[str, Any],
        source: Optional[str] = None
    ) -> str:
        """Publish an event.
        
        Args:
            event_type: Type of event to publish
            data: Event data
            source: Optional source of the event
            
        Returns:
            Event ID
        """
        event_type_str = str(event_type)
        event = Event(
            type=event_type_str,
            data=data,
            source=source
        )
        
        return await self.publish_event(event)
        
    async def publish_event(self, event: Event) -> str:
        """Publish an event object.
        
        Args:
            event: Event to publish
            
        Returns:
            Event ID
        """
        handlers = []
        
        # Get handlers for this event
        with self._lock:
            if event.type in self._handlers:
                handlers.extend(self._handlers[event.type])
                
            # Add wildcard handlers
            handlers.extend(self._wildcard_handlers)
            
        # Log the event
        self._logger.debug(f"Publishing event: {event.type} (id: {event.id})")
            
        # Execute handlers
        if handlers:
            await asyncio.gather(
                *(self._safe_execute_handler(h, event.data) for h in handlers)
            )
            
        return event.id
        
    async def _safe_execute_handler(
        self,
        handler: EventHandlerType,
        data: Dict[str, Any]
    ) -> None:
        """Execute a handler safely.
        
        Args:
            handler: Event handler function
            data: Event data
        """
        try:
            await handler(data)
        except Exception as e:
            self._logger.error(
                f"Error executing event handler {handler.__name__}: {e}",
                exc_info=True
            )
            
    def _ensure_async_handler(
        self,
        handler: Union[EventHandlerType, SyncEventHandlerType]
    ) -> EventHandlerType:
        """Ensure a handler is async.
        
        Args:
            handler: Event handler function
            
        Returns:
            Async event handler function
        """
        if asyncio.iscoroutinefunction(handler):
            return cast(EventHandlerType, handler)
            
        # Create async wrapper for sync handler
        async def async_wrapper(data: Dict[str, Any]) -> None:
            """Async wrapper for sync handler."""
            handler(data)
            
        # Copy metadata
        async_wrapper.__name__ = handler.__name__
        async_wrapper.__doc__ = handler.__doc__
        async_wrapper.__wrapped__ = handler
        
        return async_wrapper


# Global event bus
_global_event_bus = None


def get_event_bus() -> EventBus:
    """Get the global event bus.
    
    Returns:
        Global event bus
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


# Event decorators
def event_listener(event_type: Union[str, EventType]):
    """Decorator for event listeners.
    
    Args:
        event_type: Type of event to listen for
        
    Returns:
        Decorator function
    """
    def decorator(func):
        """Decorator function."""
        # Register the function as an event listener
        event_bus = get_event_bus()
        event_bus.subscribe(event_type, func)
        
        return func
        
    return decorator


def emit_event(event_type: Union[str, EventType], include_result: bool = False):
    """Decorator to emit an event before and after a function call.
    
    Args:
        event_type: Type of event to emit
        include_result: Whether to include the function result in the event data
        
    Returns:
        Decorator function
    """
    start_event = f"{event_type}.start"
    complete_event = f"{event_type}.complete"
    error_event = f"{event_type}.error"
    
    def decorator(func):
        """Decorator function."""
        if asyncio.iscoroutinefunction(func):
            @asyncio.coroutine
            async def wrapper(*args, **kwargs):
                """Async wrapper function."""
                # Get event bus
                event_bus = get_event_bus()
                
                # Prepare event data
                event_data = {
                    "function": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                
                # Emit start event
                await event_bus.publish(start_event, event_data)
                
                try:
                    # Call function
                    result = await func(*args, **kwargs)
                    
                    # Prepare complete event data
                    complete_data = dict(event_data)
                    if include_result:
                        complete_data["result"] = result
                        
                    # Emit complete event
                    await event_bus.publish(complete_event, complete_data)
                    
                    return result
                except Exception as e:
                    # Prepare error event data
                    error_data = dict(event_data)
                    error_data["error"] = str(e)
                    error_data["error_type"] = e.__class__.__name__
                    
                    # Emit error event
                    await event_bus.publish(error_event, error_data)
                    
                    # Re-raise the exception
                    raise
        else:
            def wrapper(*args, **kwargs):
                """Sync wrapper function."""
                # Get event bus
                event_bus = get_event_bus()
                
                # Prepare event data
                event_data = {
                    "function": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                
                # Emit start event (using event loop if available)
                asyncio.get_event_loop().create_task(
                    event_bus.publish(start_event, event_data)
                )
                
                try:
                    # Call function
                    result = func(*args, **kwargs)
                    
                    # Prepare complete event data
                    complete_data = dict(event_data)
                    if include_result:
                        complete_data["result"] = result
                        
                    # Emit complete event
                    asyncio.get_event_loop().create_task(
                        event_bus.publish(complete_event, complete_data)
                    )
                    
                    return result
                except Exception as e:
                    # Prepare error event data
                    error_data = dict(event_data)
                    error_data["error"] = str(e)
                    error_data["error_type"] = e.__class__.__name__
                    
                    # Emit error event
                    asyncio.get_event_loop().create_task(
                        event_bus.publish(error_event, error_data)
                    )
                    
                    # Re-raise the exception
                    raise
                    
        # Copy metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        wrapper.__wrapped__ = func
        
        return wrapper
        
    return decorator


# Monitoring components
class EventMonitor:
    """Monitor for events.
    
    This class allows monitoring events for debugging, metrics collection,
    and tracing.
    """
    
    def __init__(self):
        """Initialize event monitor."""
        self._events: List[Event] = []
        self._logger = get_logger("pepperpy.events.monitor")
        self._event_bus = get_event_bus()
        
        # Register handler for all events
        self._event_bus.subscribe("*", self._handle_event)
        
    async def _handle_event(self, data: Dict[str, Any]) -> None:
        """Handle all events.
        
        Args:
            data: Event data
        """
        # Create event object if needed
        event = Event(
            type=data["type"],
            data=data["data"],
            id=data.get("id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            source=data.get("source")
        )
        
        # Add to events list
        self._events.append(event)
        
        # Log the event
        self._logger.debug(f"Monitored event: {event.type} (id: {event.id})")
        
    def get_events(
        self,
        event_type: Optional[Union[str, EventType]] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Event]:
        """Get events matching criteria.
        
        Args:
            event_type: Optional event type filter
            source: Optional source filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of matching events
        """
        result = self._events
        
        # Apply filters
        if event_type:
            event_type_str = str(event_type)
            result = [e for e in result if e.type == event_type_str]
            
        if source:
            result = [e for e in result if e.source == source]
            
        if start_time:
            result = [e for e in result if e.timestamp >= start_time]
            
        if end_time:
            result = [e for e in result if e.timestamp <= end_time]
            
        return result
        
    def clear_events(self) -> None:
        """Clear all events."""
        self._events = []
        
    def shutdown(self) -> None:
        """Shutdown event monitor."""
        # Unregister handler
        self._event_bus.unsubscribe("*", self._handle_event)


# Global event monitor
_global_event_monitor = None


def get_event_monitor() -> EventMonitor:
    """Get the global event monitor.
    
    Returns:
        Global event monitor
    """
    global _global_event_monitor
    if _global_event_monitor is None:
        _global_event_monitor = EventMonitor()
    return _global_event_monitor


# Event context
class EventContext:
    """Context manager for event tracing."""
    
    def __init__(
        self, 
        context_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Initialize event context.
        
        Args:
            context_id: Optional context ID
            parent_id: Optional parent context ID
            attributes: Optional context attributes
        """
        self.context_id = context_id or str(uuid.uuid4())
        self.parent_id = parent_id
        self.attributes = attributes or {}
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        
    def __enter__(self) -> "EventContext":
        """Enter context.
        
        Returns:
            Context instance
        """
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        self.end_time = time.time()
        
    @property
    def duration(self) -> Optional[float]:
        """Get context duration.
        
        Returns:
            Duration in seconds or None if context is still active
        """
        if self.end_time is None:
            return None
        return self.end_time - self.start_time
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary.
        
        Returns:
            Dictionary representation of the context
        """
        result = {
            "context_id": self.context_id,
            "start_time": self.start_time,
            "attributes": self.attributes
        }
        
        if self.parent_id:
            result["parent_id"] = self.parent_id
            
        if self.end_time:
            result["end_time"] = self.end_time
            result["duration"] = self.duration
            
        return result


# Thread-local context
_context_var = threading.local()


def get_current_context() -> Optional[EventContext]:
    """Get the current event context.
    
    Returns:
        Current event context or None if no context is active
    """
    return getattr(_context_var, "current_context", None)


def set_current_context(context: Optional[EventContext]) -> None:
    """Set the current event context.
    
    Args:
        context: Event context or None to clear
    """
    _context_var.current_context = context


class TraceContext:
    """Context manager for event tracing."""
    
    def __init__(
        self, 
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None
    ):
        """Initialize trace context.
        
        Args:
            name: Trace name
            attributes: Optional trace attributes
            parent_id: Optional parent trace ID
        """
        self.name = name
        
        # Get parent context ID
        if parent_id is None:
            parent_context = get_current_context()
            if parent_context:
                parent_id = parent_context.context_id
                
        # Prepare attributes
        trace_attributes = attributes or {}
        trace_attributes["name"] = name
        
        # Create context
        self.context = EventContext(
            parent_id=parent_id,
            attributes=trace_attributes
        )
        
        # Store reference to the previous context
        self.previous_context = get_current_context()
        
    def __enter__(self) -> EventContext:
        """Enter trace context.
        
        Publishes trace.start event and sets current context.
        
        Returns:
            Event context
        """
        # Set as current context
        set_current_context(self.context)
        
        # Publish trace start event
        event_bus = get_event_bus()
        asyncio.get_event_loop().create_task(
            event_bus.publish(
                f"trace.{self.name}.start",
                {
                    "context": self.context.to_dict(),
                    "parent_id": self.context.parent_id
                }
            )
        )
        
        return self.context
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit trace context.
        
        Publishes trace.end event and restores previous context.
        """
        # End the context
        self.context.__exit__(exc_type, exc_val, exc_tb)
        
        # Publish trace end event
        event_data = {
            "context": self.context.to_dict(),
            "duration": self.context.duration
        }
        
        # Add error information if an exception occurred
        if exc_type:
            event_data["error"] = {
                "type": exc_type.__name__,
                "message": str(exc_val) if exc_val else ""
            }
            
        event_bus = get_event_bus()
        asyncio.get_event_loop().create_task(
            event_bus.publish(f"trace.{self.name}.end", event_data)
        )
        
        # Restore previous context
        set_current_context(self.previous_context)


def trace(name: str, **attributes):
    """Decorator for function tracing.
    
    Args:
        name: Trace name
        **attributes: Additional trace attributes
        
    Returns:
        Decorator function
    """
    def decorator(func):
        """Decorator function."""
        if asyncio.iscoroutinefunction(func):
            async def wrapper(*args, **kwargs):
                """Async wrapper function."""
                # Create trace context
                func_name = f"{name}.{func.__name__}" if name else func.__name__
                with TraceContext(func_name, attributes) as context:
                    return await func(*args, **kwargs)
        else:
            def wrapper(*args, **kwargs):
                """Sync wrapper function."""
                # Create trace context
                func_name = f"{name}.{func.__name__}" if name else func.__name__
                with TraceContext(func_name, attributes) as context:
                    return func(*args, **kwargs)
                    
        # Copy metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        wrapper.__wrapped__ = func
        
        return wrapper
        
    return decorator