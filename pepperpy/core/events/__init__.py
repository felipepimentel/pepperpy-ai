"""Event system for the PepperPy framework.

This module provides event handling capabilities for the framework,
allowing components to communicate through an event-based system.
"""

from pepperpy.core.events.bus import EventBus, get_event_bus
from pepperpy.core.events.types import EventType

__all__ = ["EventType", "EventBus", "get_event_bus"]
