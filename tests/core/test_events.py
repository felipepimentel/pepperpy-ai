"""Tests for the Event System.

This module contains tests for the Event System, including:
- EventBus implementation
- Event handlers and callbacks
- Event prioritization and filtering
"""

from datetime import datetime
from uuid import uuid4

import pytest

from pepperpy.core.events import Event, EventBus, EventHandler, EventPriority, EventType
from pepperpy.core.exceptions import ValidationError


class MockEventHandler(EventHandler):
    """Mock event handler for testing."""

    def __init__(self) -> None:
        self.handled_events = []

    async def handle_event(self, event: Event) -> None:
        self.handled_events.append(event)


@pytest.fixture
def event():
    """Create a test event."""
    return Event(
        id=uuid4(),
        type=EventType.SYSTEM_STARTED,
        source_id="test_source",
        timestamp=datetime.fromtimestamp(1234567890),
        data={"test": True},
    )


@pytest.fixture
def event_bus():
    """Create an event bus instance."""
    return EventBus()


async def test_event_bus_initialization(event_bus):
    """Test event bus initialization."""
    assert event_bus._handlers == {}
    assert event_bus._priorities == {}


async def test_event_handler_registration(event_bus):
    """Test event handler registration."""
    handler = MockEventHandler()

    # Register handler
    event_bus.register_handler(
        handler=handler,
        event_types=[EventType.SYSTEM_STARTED],
        priority=EventPriority.MEDIUM,
    )

    # Verify registration
    assert handler in event_bus._handlers[EventType.SYSTEM_STARTED]
    assert event_bus._priorities[handler] == EventPriority.MEDIUM


async def test_event_handler_deregistration(event_bus):
    """Test event handler deregistration."""
    handler = MockEventHandler()

    # Register and then deregister handler
    event_bus.register_handler(handler=handler, event_types=[EventType.SYSTEM_STARTED])
    event_bus.deregister_handler(handler)

    # Verify deregistration
    assert handler not in event_bus._handlers[EventType.SYSTEM_STARTED]
    assert handler not in event_bus._priorities


async def test_event_emission(event_bus, event):
    """Test event emission."""
    handler = MockEventHandler()

    # Register handler and emit event
    event_bus.register_handler(handler=handler, event_types=[event.type])
    await event_bus.emit(event)

    # Verify event was handled
    assert len(handler.handled_events) == 1
    assert handler.handled_events[0] == event


async def test_event_prioritization(event_bus, event):
    """Test event handler prioritization."""
    high_priority = MockEventHandler()
    medium_priority = MockEventHandler()
    low_priority = MockEventHandler()

    # Register handlers with different priorities
    event_bus.register_handler(
        handler=medium_priority, event_types=[event.type], priority=EventPriority.MEDIUM
    )
    event_bus.register_handler(
        handler=high_priority, event_types=[event.type], priority=EventPriority.HIGH
    )
    event_bus.register_handler(
        handler=low_priority, event_types=[event.type], priority=EventPriority.LOW
    )

    # Emit event
    await event_bus.emit(event)

    # Verify execution order
    assert len(high_priority.handled_events) == 1
    assert len(medium_priority.handled_events) == 1
    assert len(low_priority.handled_events) == 1

    # Check timestamps to verify order
    high_time = high_priority.handled_events[0].timestamp
    medium_time = medium_priority.handled_events[0].timestamp
    low_time = low_priority.handled_events[0].timestamp

    assert high_time < medium_time < low_time


async def test_event_filtering(event_bus, event):
    """Test event type filtering."""
    handler = MockEventHandler()

    # Register handler for specific event type
    event_bus.register_handler(handler=handler, event_types=[EventType.SYSTEM_STARTED])

    # Emit events of different types
    await event_bus.emit(event)  # SYSTEM_STARTED
    await event_bus.emit(
        Event(
            id=uuid4(),
            type=EventType.SYSTEM_STOPPED,
            source_id="test_source",
            timestamp=datetime.fromtimestamp(1234567890),
            data={"test": True},
        )
    )

    # Verify only matching events were handled
    assert len(handler.handled_events) == 1
    assert handler.handled_events[0].type == EventType.SYSTEM_STARTED


async def test_event_validation(event_bus):
    """Test event validation."""
    # Test invalid event type
    with pytest.raises(ValidationError):
        await event_bus.emit(
            Event(
                id=uuid4(),
                type="invalid_type",  # type: ignore
                source_id="test_source",
                timestamp=datetime.fromtimestamp(1234567890),
                data={},
            )
        )

    # Test missing required fields
    with pytest.raises(ValidationError):
        await event_bus.emit(
            Event(  # type: ignore
                type=EventType.SYSTEM_STARTED,
                source_id="test_source",
                timestamp=datetime.fromtimestamp(1234567890),
            )
        )


async def test_event_error_handling(event_bus, event):
    """Test event handler error handling."""

    class ErrorHandler(EventHandler):
        async def handle_event(self, event: Event) -> None:
            raise RuntimeError("Test error")

    handler = ErrorHandler()
    backup_handler = MockEventHandler()

    # Register both handlers
    event_bus.register_handler(handler=handler, event_types=[event.type])
    event_bus.register_handler(handler=backup_handler, event_types=[event.type])

    # Emit event - first handler should fail but not prevent second handler
    await event_bus.emit(event)

    # Verify backup handler still processed event
    assert len(backup_handler.handled_events) == 1
    assert backup_handler.handled_events[0] == event
