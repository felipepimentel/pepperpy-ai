"""Tests for event dispatcher and middleware.

This module contains tests for:
- Event dispatcher functionality
- Middleware processing chain
- Event handler subscription
"""

import pytest

from pepperpy.events.base import Event, EventHandler, EventPriority, EventType
from pepperpy.events.dispatcher import EventDispatcher
from pepperpy.events.middleware import (
    AuditMiddleware,
    ErrorHandlingMiddleware,
    EventMiddleware,
    MetricsMiddleware,
    NextMiddleware,
)


class TestEvent(Event):
    """Test event class."""

    def __init__(self, data: str) -> None:
        """Initialize test event."""
        super().__init__(
            event_type=str(EventType.SYSTEM), priority=EventPriority.NORMAL
        )
        self.data = data


class TestHandler(EventHandler):
    """Test event handler."""

    def __init__(self) -> None:
        """Initialize test handler."""
        super().__init__()
        self.handled_events = []

    async def handle_event(self, event: Event) -> None:
        """Handle test event."""
        self.handled_events.append(event)


class TestMiddleware(EventMiddleware):
    """Test middleware."""

    def __init__(self) -> None:
        """Initialize test middleware."""
        self.processed_events = []

    async def process(self, event: Event, next_middleware: "NextMiddleware") -> None:
        """Process test event."""
        self.processed_events.append(event)
        await next_middleware(event)


@pytest.fixture
async def dispatcher():
    """Create event dispatcher fixture."""
    dispatcher = EventDispatcher()
    await dispatcher.initialize()
    yield dispatcher
    await dispatcher.cleanup()


@pytest.fixture
def handler():
    """Create test handler fixture."""
    return TestHandler()


@pytest.fixture
def middleware():
    """Create test middleware fixture."""
    return TestMiddleware()


async def test_handler_subscription(dispatcher, handler):
    """Test handler subscription and event dispatch."""
    event = TestEvent("test")
    dispatcher.subscribe(event.event_type, handler)

    await dispatcher.dispatch(event)

    assert len(handler.handled_events) == 1
    assert handler.handled_events[0] == event


async def test_handler_unsubscription(dispatcher, handler):
    """Test handler unsubscription."""
    event = TestEvent("test")
    dispatcher.subscribe(event.event_type, handler)
    dispatcher.unsubscribe(event.event_type, handler)

    await dispatcher.dispatch(event)

    assert len(handler.handled_events) == 0


async def test_middleware_chain(dispatcher, handler, middleware):
    """Test middleware processing chain."""
    event = TestEvent("test")
    dispatcher.subscribe(event.event_type, handler)
    dispatcher.add_middleware(middleware)

    await dispatcher.dispatch(event)

    assert len(middleware.processed_events) == 1
    assert middleware.processed_events[0] == event
    assert len(handler.handled_events) == 1
    assert handler.handled_events[0] == event


async def test_middleware_removal(dispatcher, handler, middleware):
    """Test middleware removal."""
    event = TestEvent("test")
    dispatcher.subscribe(event.event_type, handler)
    dispatcher.add_middleware(middleware)
    dispatcher.remove_middleware(middleware)

    await dispatcher.dispatch(event)

    assert len(middleware.processed_events) == 0
    assert len(handler.handled_events) == 1


async def test_multiple_handlers(dispatcher):
    """Test multiple handlers for same event type."""
    handler1 = TestHandler()
    handler2 = TestHandler()
    event = TestEvent("test")

    dispatcher.subscribe(event.event_type, handler1)
    dispatcher.subscribe(event.event_type, handler2)
    await dispatcher.dispatch(event)

    assert len(handler1.handled_events) == 1
    assert len(handler2.handled_events) == 1


async def test_multiple_middleware(dispatcher, handler):
    """Test multiple middleware in chain."""
    middleware1 = TestMiddleware()
    middleware2 = TestMiddleware()
    event = TestEvent("test")

    dispatcher.subscribe(event.event_type, handler)
    dispatcher.add_middleware(middleware1)
    dispatcher.add_middleware(middleware2)
    await dispatcher.dispatch(event)

    assert len(middleware1.processed_events) == 1
    assert len(middleware2.processed_events) == 1
    assert len(handler.handled_events) == 1


async def test_error_handling_middleware(dispatcher, handler):
    """Test error handling middleware."""
    error_middleware = ErrorHandlingMiddleware()
    await error_middleware.initialize()

    class ErrorHandler(EventHandler):
        async def handle_event(self, event: Event) -> None:
            raise ValueError("Test error")

    error_handler = ErrorHandler()
    event = TestEvent("test")

    dispatcher.subscribe(event.event_type, error_handler)
    dispatcher.add_middleware(error_middleware)
    await dispatcher.dispatch(event)

    # Event should be processed without raising exception
    assert True


async def test_metrics_middleware(dispatcher, handler):
    """Test metrics middleware."""
    metrics_middleware = MetricsMiddleware()
    await metrics_middleware.initialize()

    event = TestEvent("test")
    dispatcher.subscribe(event.event_type, handler)
    dispatcher.add_middleware(metrics_middleware)
    await dispatcher.dispatch(event)

    assert len(handler.handled_events) == 1


async def test_audit_middleware(dispatcher, handler):
    """Test audit middleware."""
    audit_middleware = AuditMiddleware()
    await audit_middleware.initialize()

    event = TestEvent("test")
    dispatcher.subscribe(event.event_type, handler)
    dispatcher.add_middleware(audit_middleware)
    await dispatcher.dispatch(event)

    assert len(handler.handled_events) == 1
