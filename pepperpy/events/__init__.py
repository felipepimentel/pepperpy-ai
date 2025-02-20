"""Event system for the Pepperpy framework.

This module provides a comprehensive event system with:
- Event bus implementation
- Event handlers and callbacks
- Event prioritization
- Event filtering
- Lifecycle hooks
"""

from pepperpy.events.base import (
    Event,
    EventBus,
    EventEmitter,
    EventFilter,
    EventHandler,
    EventMetrics,
    EventPriority,
    EventType,
)
from pepperpy.events.handlers import (
    RegistryEvent,
    RegistryEventHandler,
)
from pepperpy.events.hooks import (
    HookCallback,
    HookManager,
    hook_manager,
)

__all__ = [
    # Base event system
    "Event",
    "EventBus",
    "EventEmitter",
    "EventFilter",
    "EventHandler",
    "EventMetrics",
    "EventPriority",
    "EventType",
    # Registry event handlers
    "RegistryEvent",
    "RegistryEventHandler",
    # Hook system
    "HookCallback",
    "HookManager",
    "hook_manager",
]
