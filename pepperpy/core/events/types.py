"""Event types for the PepperPy framework.

This module defines the types of events that can be emitted in the system.
"""

from enum import Enum, auto


class EventType(Enum):
    """Types of events that can be emitted in the system."""

    # Lifecycle events
    INITIALIZE = auto()
    START = auto()
    STOP = auto()
    CLEANUP = auto()

    # Processing events
    PROCESS_START = auto()
    PROCESS_COMPLETE = auto()
    PROCESS_ERROR = auto()

    # Resource events
    RESOURCE_ACQUIRED = auto()
    RESOURCE_RELEASED = auto()

    # Custom events
    CUSTOM = auto()
