"""Event system for the Pepperpy framework.

This module provides event types and handlers for the framework.
"""

from pepperpy.core.events.bus import EventBus
from pepperpy.core.events.handlers import EventHandler
from pepperpy.core.events.handlers.registry import RegistryEvent, RegistryEventHandler
from pepperpy.core.events.types import EventType

__all__ = [
    "EventBus",
    "EventHandler",
    "EventType",
    "RegistryEvent",
    "RegistryEventHandler",
]
