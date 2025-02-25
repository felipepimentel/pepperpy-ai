"""Component state definitions for the Pepperpy framework.

This module defines the various states that components can be in.
"""

from enum import Enum, auto


class ComponentState(str, Enum):
    """States a component can be in."""

    UNREGISTERED = "unregistered"
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    CLEANING = "cleaning"
    CLEANED = "cleaned"
    EXECUTING = "executing"


__all__ = ["ComponentState"]
