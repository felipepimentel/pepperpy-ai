"""Event bus implementation.

This module provides functionality for event-driven communication,
including event publishing, subscription, and filtering.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set
import logging

from ...core.errors import PepperpyError
from ...interfaces import BaseProvider
from .event import Event, EventFilter, EventHandler

logger = logging.getLogger(__name__)

class EventBusError(PepperpyError):
    """Event bus error."""
    pass

class EventBus(BaseProvider):
    """Event bus implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize bus.
        
        Args:
            name: Bus name
            config: Optional configuration
        """
        super().__init__(
            name=name,
            config=config,
        )
        self._handlers: Dict[str, Set[EventHandler]] = {}
        self._filters: Dict[str, List[EventFilter]] = {}
        self._lock = asyncio.Lock()
        
    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        filters: Optional[List[EventFilter]] = None,
    ) -> None:
        """Subscribe to events.
        
        Args:
            event_type: Event type
            handler: Event handler
            filters: Optional event filters
            
        Raises:
            EventBusError: If subscription fails
        """
        if not event_type:
            raise EventBusError("Empty event type")
            
        if not handler:
            raise EventBusError("Missing event handler")
            
        if event_type not in self._handlers:
            self._handlers[event_type] = set()
            self._filters[event_type] = []
            
        self._handlers[event_type].add(handler)
        
        if filters:
            self._filters[event_type].extend(filters)
            
    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Unsubscribe from events.
        
        Args:
            event_type: Event type
            handler: Event handler
            
        Raises:
            EventBusError: If unsubscription fails
        """
        if not event_type:
            raise EventBusError("Empty event type")
            
        if not handler:
            raise EventBusError("Missing event handler")
            
        if event_type not in self._handlers:
            return
            
        self._handlers[event_type].discard(handler)
        
        if not self._handlers[event_type]:
            del self._handlers[event_type]
            del self._filters[event_type]
            
    async def publish(self, event: Event) -> None:
        """Publish event.
        
        Args:
            event: Event to publish
            
        Raises:
            EventBusError: If publishing fails
        """
        if not event:
            raise EventBusError("Missing event")
            
        if not event.type:
            raise EventBusError("Empty event type")
            
        if event.type not in self._handlers:
            return
            
        async with self._lock:
            # Apply filters
            filters = self._filters[event.type]
            if filters and not all(f.matches(event) for f in filters):
                return
                
            # Notify handlers
            handlers = self._handlers[event.type]
            tasks = [h.handle(event) for h in handlers]
            
            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                raise EventBusError(f"Event handling failed: {e}")
                
    async def _initialize_impl(self) -> None:
        """Initialize bus."""
        pass
        
    async def _cleanup_impl(self) -> None:
        """Clean up bus."""
        self._handlers.clear()
        self._filters.clear()
        
    async def validate(self) -> None:
        """Validate bus state."""
        if not self.name:
            raise EventBusError("Empty bus name") 