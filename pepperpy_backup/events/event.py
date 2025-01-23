"""Event implementation.

This module provides functionality for defining and handling events,
including event filtering and transformation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Protocol

from pepperpy.common.errors import PepperpyError


class EventError(PepperpyError):
    """Event error."""
    pass


@dataclass
class Event:
    """Event data."""
    
    type: str
    """Event type."""
    
    source: str
    """Event source."""
    
    timestamp: datetime
    """Event timestamp."""
    
    data: Dict[str, Any]
    """Event data."""
    
    metadata: Optional[Dict[str, Any]] = None
    """Optional event metadata."""
    
    def __post_init__(self) -> None:
        """Validate event."""
        if not self.type:
            raise EventError("Empty event type")
            
        if not self.source:
            raise EventError("Empty event source")
            
        if not self.timestamp:
            raise EventError("Missing event timestamp")
            
        if not self.data:
            raise EventError("Missing event data")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Event dictionary
        """
        return {
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata or {},
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create from dictionary.
        
        Args:
            data: Event dictionary
            
        Returns:
            Event instance
            
        Raises:
            EventError: If creation fails
        """
        try:
            return cls(
                type=data["type"],
                source=data["source"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                data=data["data"],
                metadata=data.get("metadata"),
            )
        except Exception as e:
            raise EventError(f"Event creation failed: {e}")


class EventFilter(Protocol):
    """Event filter interface."""
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter.
        
        Args:
            event: Event to check
            
        Returns:
            True if matches, False otherwise
        """
        ...


class EventTransformer(Protocol):
    """Event transformer interface."""
    
    def transform(self, event: Event) -> Event:
        """Transform event.
        
        Args:
            event: Event to transform
            
        Returns:
            Transformed event
            
        Raises:
            EventError: If transformation fails
        """
        ...


class EventHandler(Protocol):
    """Event handler interface."""
    
    async def handle(self, event: Event) -> None:
        """Handle event.
        
        Args:
            event: Event to handle
            
        Raises:
            EventError: If handling fails
        """
        ... 