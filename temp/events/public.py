"""Public interfaces for PepperPy Events module.

This module provides a stable public interface for the events functionality.
It exposes the core event abstractions and functions that are considered part
of the public API.
"""

from pepperpy.events.core import (
    AsyncEventHandler,
    AsyncEventHandlerAdapter,
    Event,
    EventBus,
    EventHandler,
    EventHandlerAdapter,
    EventPriority,
    emit,
    emit_async,
    get_event_bus,
    off,
    off_all,
    on,
    on_async,
)

# Re-export everything
__all__ = [
    # Classes
    "AsyncEventHandler",
    "AsyncEventHandlerAdapter",
    "Event",
    "EventBus",
    "EventHandler",
    "EventHandlerAdapter",
    "EventPriority",
    # Functions
    "emit",
    "emit_async",
    "get_event_bus",
    "off",
    "off_all",
    "on",
    "on_async",
]
