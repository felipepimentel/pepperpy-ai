"""Event type definitions.

This module provides type definitions for the event system, including
event data structures and protocols.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from pepperpy.common.errors import PepperpyError


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


class EventFilter(Protocol):
    """Event filter protocol."""
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter.
        
        Args:
            event: Event to check
            
        Returns:
            True if event matches filter, False otherwise
        """
        ...


class EventTransformer(Protocol):
    """Event transformer protocol."""
    
    def transform(self, event: Event) -> Event:
        """Transform event.
        
        Args:
            event: Event to transform
            
        Returns:
            Transformed event
        """
        ...


class EventValidator(Protocol):
    """Event validator protocol."""
    
    def validate(self, event: Event) -> bool:
        """Validate event.
        
        Args:
            event: Event to validate
            
        Returns:
            True if event is valid, False otherwise
        """
        ...
