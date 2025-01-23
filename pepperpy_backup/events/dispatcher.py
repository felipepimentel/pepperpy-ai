"""Event dispatcher functionality.

This module provides functionality for dispatching events to registered
handlers based on event types and filtering rules.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from .handler import EventHandler
from .types import Event


logger = logging.getLogger(__name__)


class DispatcherError(PepperpyError):
    """Dispatcher error."""
    pass


class EventDispatcher(Lifecycle):
    """Event dispatcher implementation."""
    
    def __init__(self, name: str):
        """Initialize dispatcher.
        
        Args:
            name: Dispatcher name
        """
        super().__init__()
        self.name = name
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False
        
    def register_handler(self, event_type: str, handler: EventHandler) -> None:
        """Register event handler.
        
        Args:
            event_type: Event type to handle
            handler: Handler to register
            
        Raises:
            DispatcherError: If handler already registered
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            
        if handler in self._handlers[event_type]:
            raise DispatcherError(
                f"Handler already registered for event type: {event_type}"
            )
            
        self._handlers[event_type].append(handler)
        
    def unregister_handler(self, event_type: str, handler: EventHandler) -> None:
        """Unregister event handler.
        
        Args:
            event_type: Event type to unregister from
            handler: Handler to unregister
            
        Raises:
            DispatcherError: If handler not registered
        """
        if event_type not in self._handlers:
            raise DispatcherError(f"No handlers for event type: {event_type}")
            
        if handler not in self._handlers[event_type]:
            raise DispatcherError(
                f"Handler not registered for event type: {event_type}"
            )
            
        self._handlers[event_type].remove(handler)
        
    async def dispatch(self, event: Event) -> None:
        """Dispatch event to queue.
        
        Args:
            event: Event to dispatch
        """
        await self._queue.put(event)
        
    async def _process_events(self) -> None:
        """Process events from queue."""
        while self._running:
            try:
                event = await self._queue.get()
                
                if event.name not in self._handlers:
                    logger.warning(f"No handlers for event type: {event.name}")
                    continue
                    
                tasks = []
                for handler in self._handlers[event.name]:
                    tasks.append(handler.handle(event))
                    
                await asyncio.gather(*tasks)
                
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
                
            finally:
                self._queue.task_done()
                
    async def _initialize(self) -> None:
        """Initialize dispatcher."""
        self._running = True
        asyncio.create_task(self._process_events())
        
    async def _cleanup(self) -> None:
        """Clean up dispatcher."""
        self._running = False
        await self._queue.join()
        
    def validate(self) -> None:
        """Validate dispatcher state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Dispatcher name cannot be empty")
