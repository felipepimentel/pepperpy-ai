"""Tests for the core event system."""

import asyncio
import pytest
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pepperpy.events import (
    Event,
    EventBus,
    EventHandler,
    EventListener,
    SYSTEM_STARTED,
    SYSTEM_ERROR,
)


class TestEvent:
    """Test event data model."""

    def test_event_creation(self):
        """Test creating an event."""
        event = Event(
            type=SYSTEM_STARTED,
            data={"message": "System started"},
        )
        
        assert isinstance(event.id, UUID)
        assert event.type == SYSTEM_STARTED
        assert event.data == {"message": "System started"}
        assert isinstance(event.timestamp, datetime)
        assert event.metadata == {}

    def test_event_immutability(self):
        """Test that events are immutable."""
        event = Event(
            type=SYSTEM_STARTED,
            data={"message": "System started"},
        )
        
        with pytest.raises(Exception):
            event.type = SYSTEM_ERROR
            
        with pytest.raises(Exception):
            event.data["message"] = "Changed"


class TestEventHandler:
    """Test event handlers."""

    class TestHandler(EventHandler[Event[dict]]):
        """Test handler implementation."""
        
        def __init__(self):
            """Initialize handler."""
            self.events: List[Event[dict]] = []
            
        async def handle(self, event: Event[dict]) -> None:
            """Handle event."""
            self.events.append(event)

    @pytest.mark.asyncio
    async def test_handler_subscription(self):
        """Test subscribing and unsubscribing handlers."""
        bus = EventBus()
        handler = self.TestHandler()
        
        # Initialize bus
        await bus.initialize()
        
        try:
            # Subscribe handler
            bus.subscribe_handler(SYSTEM_STARTED, handler)
            
            # Publish event
            event = Event(
                type=SYSTEM_STARTED,
                data={"message": "System started"},
            )
            await bus.publish(event)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Verify handler was called
            assert len(handler.events) == 1
            assert handler.events[0].id == event.id
            
            # Unsubscribe handler
            bus.unsubscribe_handler(SYSTEM_STARTED, handler)
            
            # Publish another event
            event2 = Event(
                type=SYSTEM_STARTED,
                data={"message": "System started again"},
            )
            await bus.publish(event2)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Verify handler wasn't called
            assert len(handler.events) == 1
            
        finally:
            await bus.cleanup()


class TestEventListener:
    """Test event listeners."""

    class TestListener(EventListener[Event[dict]]):
        """Test listener implementation."""
        
        def __init__(self):
            """Initialize listener."""
            self.events: List[Event[dict]] = []
            
        async def on_event(self, event: Event[dict]) -> None:
            """Handle event."""
            self.events.append(event)

    @pytest.mark.asyncio
    async def test_listener_subscription(self):
        """Test subscribing and unsubscribing listeners."""
        bus = EventBus()
        listener = self.TestListener()
        
        # Initialize bus
        await bus.initialize()
        
        try:
            # Subscribe listener
            bus.subscribe_listener(SYSTEM_STARTED, listener)
            
            # Publish event
            event = Event(
                type=SYSTEM_STARTED,
                data={"message": "System started"},
            )
            await bus.publish(event)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Verify listener was called
            assert len(listener.events) == 1
            assert listener.events[0].id == event.id
            
            # Unsubscribe listener
            bus.unsubscribe_listener(SYSTEM_STARTED, listener)
            
            # Publish another event
            event2 = Event(
                type=SYSTEM_STARTED,
                data={"message": "System started again"},
            )
            await bus.publish(event2)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Verify listener wasn't called
            assert len(listener.events) == 1
            
        finally:
            await bus.cleanup()


class TestEventBus:
    """Test event bus functionality."""

    @pytest.mark.asyncio
    async def test_event_bus_lifecycle(self):
        """Test event bus initialization and cleanup."""
        bus = EventBus()
        
        # Test initialization
        assert bus._state.value == "CREATED"
        await bus.initialize()
        assert bus._state.value == "READY"
        
        # Test cleanup
        await bus.cleanup()
        assert bus._state.value == "CLEANED"

    @pytest.mark.asyncio
    async def test_multiple_handlers_and_listeners(self):
        """Test multiple handlers and listeners for same event."""
        bus = EventBus()
        handler1 = TestEventHandler.TestHandler()
        handler2 = TestEventHandler.TestHandler()
        listener1 = TestEventListener.TestListener()
        listener2 = TestEventListener.TestListener()
        
        # Initialize bus
        await bus.initialize()
        
        try:
            # Subscribe handlers and listeners
            bus.subscribe_handler(SYSTEM_STARTED, handler1)
            bus.subscribe_handler(SYSTEM_STARTED, handler2)
            bus.subscribe_listener(SYSTEM_STARTED, listener1)
            bus.subscribe_listener(SYSTEM_STARTED, listener2)
            
            # Publish event
            event = Event(
                type=SYSTEM_STARTED,
                data={"message": "System started"},
            )
            await bus.publish(event)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Verify all handlers and listeners were called
            assert len(handler1.events) == 1
            assert len(handler2.events) == 1
            assert len(listener1.events) == 1
            assert len(listener2.events) == 1
            
        finally:
            await bus.cleanup()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in event processing."""
        
        class ErrorHandler(EventHandler[Event[dict]]):
            """Handler that raises an error."""
            
            async def handle(self, event: Event[dict]) -> None:
                """Handle event."""
                raise ValueError("Test error")

        bus = EventBus()
        handler = ErrorHandler()
        normal_handler = TestEventHandler.TestHandler()
        
        # Initialize bus
        await bus.initialize()
        
        try:
            # Subscribe handlers
            bus.subscribe_handler(SYSTEM_STARTED, handler)
            bus.subscribe_handler(SYSTEM_STARTED, normal_handler)
            
            # Publish event
            event = Event(
                type=SYSTEM_STARTED,
                data={"message": "System started"},
            )
            await bus.publish(event)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Verify normal handler was still called
            assert len(normal_handler.events) == 1
            
        finally:
            await bus.cleanup() 