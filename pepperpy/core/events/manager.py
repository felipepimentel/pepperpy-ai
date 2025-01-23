"""Event manager implementation."""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle
from .base import Event, EventBus, EventError, EventHandler


logger = logging.getLogger(__name__)


class EventManager(Lifecycle):
    """Event manager implementation."""
    
    def __init__(
        self,
        name: str,
        event_bus: Optional[EventBus] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize event manager.
        
        Args:
            name: Event manager name
            event_bus: Optional event bus
            config: Optional event manager configuration
        """
        super().__init__(name)
        self._event_bus = event_bus or EventBus()
        self._config = config or {}
        self._event_types: Set[str] = set()
        
    @property
    def event_bus(self) -> EventBus:
        """Return event bus."""
        return self._event_bus
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return event manager configuration."""
        return self._config
        
    @property
    def event_types(self) -> Set[str]:
        """Return registered event types."""
        return self._event_types
        
    async def _initialize(self) -> None:
        """Initialize event manager."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up event manager."""
        pass
        
    def register_event_type(self, event_type: str) -> None:
        """Register event type.
        
        Args:
            event_type: Event type to register
            
        Raises:
            EventError: If event type already exists
        """
        if event_type in self._event_types:
            raise EventError(f"Event type {event_type} already exists")
            
        self._event_types.add(event_type)
        
    def unregister_event_type(self, event_type: str) -> None:
        """Unregister event type.
        
        Args:
            event_type: Event type to unregister
            
        Raises:
            EventError: If event type does not exist
        """
        if event_type not in self._event_types:
            raise EventError(f"Event type {event_type} does not exist")
            
        self._event_types.remove(event_type)
        
    def has_event_type(self, event_type: str) -> bool:
        """Check if event type exists.
        
        Args:
            event_type: Event type to check
            
        Returns:
            True if event type exists, False otherwise
        """
        return event_type in self._event_types
        
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Event handler
            
        Raises:
            EventError: If event type does not exist
        """
        if event_type not in self._event_types:
            raise EventError(f"Event type {event_type} does not exist")
            
        self._event_bus.subscribe(event_type, handler)
        
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from event type.
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Event handler
            
        Raises:
            EventError: If event type does not exist
        """
        if event_type not in self._event_types:
            raise EventError(f"Event type {event_type} does not exist")
            
        self._event_bus.unsubscribe(event_type, handler)
        
    async def publish(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Publish event.
        
        Args:
            event_type: Event type
            source: Event source
            data: Event data
            metadata: Optional event metadata
            
        Returns:
            Published event
            
        Raises:
            EventError: If event type does not exist
        """
        if event_type not in self._event_types:
            raise EventError(f"Event type {event_type} does not exist")
            
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            timestamp=datetime.utcnow(),
            data=data,
            metadata=metadata,
        )
        
        await self._event_bus.publish(event)
        return event
        
    def get_handlers(self, event_type: str) -> List[EventHandler]:
        """Get handlers for event type.
        
        Args:
            event_type: Event type
            
        Returns:
            List of event handlers
            
        Raises:
            EventError: If event type does not exist
        """
        if event_type not in self._event_types:
            raise EventError(f"Event type {event_type} does not exist")
            
        return self._event_bus.get_handlers(event_type)
        
    def validate(self) -> None:
        """Validate event manager state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Event manager name cannot be empty") 