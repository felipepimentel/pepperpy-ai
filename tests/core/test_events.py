"""Tests for the Event System.

This module contains tests for the Event System, including:
- EventBus implementation
- Event handlers and callbacks
- Event prioritization and filtering
"""

from datetime import datetime
from uuid import uuid4

import pytest

from pepperpy.core.errors import ValidationError
from pepperpy.core.events import Event, EventBus, EventHandler, EventType


class MockEventHandler(EventHandler):
    """Mock event handler for testing."""

    def __init__(self) -> None:
        self.handled_events = []

    async def handle_event(self, event: Event) -> None:
        self.handled_events.append(event)


class ErrorEventHandler(EventHandler):
    """Event handler that raises an error for testing."""

    async def handle_event(self, event: Event) -> None:
        raise RuntimeError("Test error")


@pytest.fixture
def event():
    """Create a test event."""
    return Event(
        id=uuid4(),
        type=EventType.SYSTEM,
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
        event_types=[EventType.SYSTEM],
    )

    # Verify registration
    assert handler in event_bus._handlers[EventType.SYSTEM]


async def test_event_handler_deregistration(event_bus):
    """Test event handler deregistration."""
    handler = MockEventHandler()

    # Register and then deregister handler
    event_bus.register_handler(handler=handler, event_types=[EventType.SYSTEM])
    event_bus.deregister_handler(handler)

    # Verify deregistration
    assert handler not in event_bus._handlers[EventType.SYSTEM]
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


async def test_event_filtering(event_bus, event):
    """Test event type filtering."""
    handler = MockEventHandler()

    # Register handler for specific event type
    event_bus.register_handler(handler=handler, event_types=[EventType.SYSTEM])

    # Emit events of different types
    await event_bus.emit(event)  # SYSTEM
    await event_bus.emit(
        Event(
            id=uuid4(),
            type=EventType.USER,
            timestamp=datetime.fromtimestamp(1234567890),
            data={"test": True},
        )
    )

    # Verify only matching events were handled
    assert len(handler.handled_events) == 1
    assert handler.handled_events[0].type == EventType.SYSTEM


async def test_event_validation(event_bus):
    """Test event validation."""
    # Test invalid event type
    with pytest.raises(ValidationError):
        await event_bus.emit(
            Event(
                id=uuid4(),
                type="invalid_type",  # type: ignore
                timestamp=datetime.fromtimestamp(1234567890),
                data={},
            )
        )

    # Test missing required fields
    with pytest.raises(ValidationError):
        await event_bus.emit(
            Event(  # type: ignore
                type=EventType.SYSTEM,
                timestamp=datetime.fromtimestamp(1234567890),
            )
        )

    # Test invalid data type
    with pytest.raises(ValidationError):
        await event_bus.emit(
            Event(
                id=uuid4(),
                type=EventType.SYSTEM,
                timestamp=datetime.fromtimestamp(1234567890),
                data=123,  # type: ignore
            )
        )


async def test_event_error_handling(event_bus, event):
    """Test event handler error handling."""
    handler = ErrorEventHandler()
    backup_handler = MockEventHandler()

    # Register both handlers
    event_bus.register_handler(handler=handler, event_types=[event.type])
    event_bus.register_handler(handler=backup_handler, event_types=[event.type])

    # Emit event - first handler should fail but not prevent second handler
    await event_bus.emit(event)

    # Verify backup handler still processed event
    assert len(backup_handler.handled_events) == 1
    assert backup_handler.handled_events[0] == event


async def test_multiple_event_types(event_bus):
    """Test handling multiple event types."""
    handler = MockEventHandler()
    event_types = [EventType.SYSTEM, EventType.USER]

    # Register handler for multiple event types
    event_bus.register_handler(handler=handler, event_types=event_types)

    # Emit events of different types
    events = [
        Event(
            id=uuid4(),
            type=event_type,
            timestamp=datetime.fromtimestamp(1234567890),
            data={"test": True},
        )
        for event_type in event_types
    ]

    for event in events:
        await event_bus.emit(event)

    # Verify all events were handled
    assert len(handler.handled_events) == len(events)
    assert all(event in handler.handled_events for event in events)


async def test_event_timestamp_validation(event_bus):
    """Test event timestamp validation."""
    # Test future timestamp
    future_time = datetime.now().timestamp() + 3600
    with pytest.raises(ValidationError):
        await event_bus.emit(
            Event(
                id=uuid4(),
                type=EventType.SYSTEM,
                timestamp=datetime.fromtimestamp(future_time),
                data={},
            )
        )

    # Test invalid timestamp format
    with pytest.raises(ValidationError):
        await event_bus.emit(
            Event(
                id=uuid4(),
                type=EventType.SYSTEM,
                timestamp="invalid",  # type: ignore
                data={},
            )
        )
