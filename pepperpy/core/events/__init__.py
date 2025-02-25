"""Event management system.

This module provides event management functionality:
- Event registration and dispatch
- Event filtering and routing
- Event monitoring and metrics
- Event lifecycle management
"""

from pepperpy.core.events.manager import Event, EventHandler, EventManager

# Export public API
__all__ = [
    "Event",
    "EventHandler",
    "EventManager",
]
