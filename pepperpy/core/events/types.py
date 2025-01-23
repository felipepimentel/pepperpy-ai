"""Event type definitions.

This module provides type definitions for the event system, including
event data structures and protocols.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from pepperpy.common.errors import PepperpyError
from pepperpy.interfaces import EventFilter, EventTransformer

class EventError(PepperpyError):
    """Event error."""
    pass

@dataclass
class Event:
    """Base event class."""
    
    name: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

__all__ = [
    "EventError",
    "Event",
    # Re-exported from interfaces
    "EventFilter",
    "EventTransformer",
]
