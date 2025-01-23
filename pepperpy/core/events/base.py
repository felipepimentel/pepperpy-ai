"""Base events implementation."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ..common.errors import PepperpyError


logger = logging.getLogger(__name__)


class EventError(PepperpyError):
    """Event error."""
    pass


@dataclass
class Event:
    """Event implementation."""
    
    id: str
    type: str
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.
        
        Returns:
            Event as dictionary
        """
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary.
        
        Args:
            data: Event data
            
        Returns:
            Event instance
        """
        return cls(
            id=data["id"],
            type=data["type"],
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            metadata=data.get("metadata"),
        )


T = TypeVar("T", bound=Event)


class EventHandler(Protocol[T]):
    """Event handler protocol."""
    
    async def handle(self, event: T) -> None:
        """Handle event.
        
        Args:
            event: Event to handle
        """
        pass


class EventBus:
    """Event bus implementation."""
    
    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: Dict[str, List[EventHandler]] = {}
        
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Event handler
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            
        self._handlers[event_type].append(handler)
        
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from event type.
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Event handler
            
        Raises:
            EventError: If event type does not exist or handler is not subscribed
        """
        if event_type not in self._handlers:
            raise EventError(f"Event type {event_type} does not exist")
            
        try:
            self._handlers[event_type].remove(handler)
        except ValueError:
            raise EventError(f"Handler not subscribed to event type {event_type}")
            
        if not self._handlers[event_type]:
            del self._handlers[event_type]
            
    async def publish(self, event: Event) -> None:
        """Publish event.
        
        Args:
            event: Event to publish
        """
        if event.type not in self._handlers:
            return
            
        for handler in self._handlers[event.type]:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(f"Error handling event {event.id}: {e}")
                
    def get_handlers(self, event_type: str) -> List[EventHandler]:
        """Get handlers for event type.
        
        Args:
            event_type: Event type
            
        Returns:
            List of event handlers
        """
        return self._handlers.get(event_type, []) 