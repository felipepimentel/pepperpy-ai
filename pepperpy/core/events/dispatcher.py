"""Event dispatcher functionality.

This module provides functionality for dispatching events to registered
handlers based on event types and filtering rules.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from ..interfaces import Provider, EventFilter, EventTransformer
from .types import Event, EventError

logger = logging.getLogger(__name__)

class DispatcherError(EventError):
    """Dispatcher error."""
    pass

class EventDispatcher(Provider):
    """Event dispatcher implementation."""
    
    def __init__(self, name: str):
        """Initialize dispatcher.
        
        Args:
            name: Dispatcher name
        """
        self.name = name
        self._handlers: Dict[str, List[EventFilter]] = {}
        self._transformers: List[EventTransformer] = []
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the dispatcher."""
        if self._initialized:
            return
            
        try:
            self._running = True
            self._initialized = True
            asyncio.create_task(self._process_queue())
        except Exception as e:
            logger.error(f"Failed to initialize dispatcher: {str(e)}")
            await self.cleanup()
            raise DispatcherError(f"Dispatcher initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up dispatcher resources."""
        self._running = False
        self._initialized = False
        self._handlers.clear()
        self._transformers.clear()
        
        # Wait for queue to be processed
        if not self._queue.empty():
            try:
                await asyncio.wait_for(self._queue.join(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for queue to be processed")
    
    def register_handler(self, event_type: str, handler: EventFilter) -> None:
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
    
    def register_transformer(self, transformer: EventTransformer) -> None:
        """Register event transformer.
        
        Args:
            transformer: Transformer to register
            
        Raises:
            DispatcherError: If transformer already registered
        """
        if transformer in self._transformers:
            raise DispatcherError("Transformer already registered")
            
        self._transformers.append(transformer)
    
    def unregister_handler(self, event_type: str, handler: EventFilter) -> None:
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
    
    def unregister_transformer(self, transformer: EventTransformer) -> None:
        """Unregister event transformer.
        
        Args:
            transformer: Transformer to unregister
            
        Raises:
            DispatcherError: If transformer not registered
        """
        if transformer not in self._transformers:
            raise DispatcherError("Transformer not registered")
            
        self._transformers.remove(transformer)
    
    async def dispatch(self, event: Event) -> None:
        """Dispatch event.
        
        Args:
            event: Event to dispatch
            
        Raises:
            DispatcherError: If dispatcher not initialized
        """
        if not self._initialized:
            raise DispatcherError("Dispatcher not initialized")
            
        await self._queue.put(event)
    
    async def _process_queue(self) -> None:
        """Process event queue."""
        while self._running:
            try:
                event = await self._queue.get()
                
                # Apply transformers
                for transformer in self._transformers:
                    try:
                        event = transformer.transform(event)
                    except Exception as e:
                        logger.error(f"Transformer failed: {str(e)}")
                        continue
                
                # Dispatch to handlers
                if event.name in self._handlers:
                    for handler in self._handlers[event.name]:
                        try:
                            if handler.matches(event):
                                await self._handle_event(handler, event)
                        except Exception as e:
                            logger.error(f"Handler failed: {str(e)}")
                            continue
                
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event processing failed: {str(e)}")
                continue
    
    async def _handle_event(self, handler: EventFilter, event: Event) -> None:
        """Handle event with handler.
        
        Args:
            handler: Handler to use
            event: Event to handle
        """
        try:
            handler.matches(event)
        except Exception as e:
            logger.error(f"Handler failed: {str(e)}")
            raise
