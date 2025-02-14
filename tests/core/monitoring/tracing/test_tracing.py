"""Tests for tracing functionality."""

import asyncio
from datetime import datetime, timedelta

import pytest

from pepperpy.core.monitoring.tracing import SpanContext, TracingManager


@pytest.mark.asyncio
async def test_span_context_creation(test_context: SpanContext):
    """Test span context creation."""
    assert test_context.trace_id == "test-trace-1"
    assert test_context.span_id == "test-span-1"
    assert test_context.parent_id is None
    assert test_context.baggage == {"app": "test"}


@pytest.mark.asyncio
async def test_span_lifecycle(tracing_manager: TracingManager):
    """Test span lifecycle management."""
    async with tracing_manager.span("root-operation") as root_span:
        assert root_span.name == "root-operation"
        assert root_span.context.parent_id is None
        assert root_span.start_time is not None
        assert root_span.end_time is None

        async with tracing_manager.span("child-operation") as child_span:
            assert child_span.name == "child-operation"
            assert child_span.context.parent_id == root_span.context.span_id
            assert child_span.start_time is not None
            assert child_span.end_time is None

            child_span.add_event("processing")

        assert child_span.end_time is not None
        assert child_span.end_time > child_span.start_time

    assert root_span.end_time is not None
    assert root_span.end_time > root_span.start_time


@pytest.mark.asyncio
async def test_span_duration(tracing_manager: TracingManager):
    """Test span duration tracking."""
    async with tracing_manager.span("duration-test") as span:
        start = datetime.utcnow()
        await asyncio.sleep(0.1)  # Simulate work
        end = datetime.utcnow()

    assert span.end_time is not None
    duration = span.end_time - span.start_time
    assert timedelta(seconds=0.1) <= duration <= (end - start)


@pytest.mark.asyncio
async def test_span_attributes(tracing_manager: TracingManager):
    """Test span attribute management."""
    async with tracing_manager.span("test-operation") as span:
        # Test basic attribute setting
        span.attributes = {"service.name": "test-service", "environment": "testing"}
        assert span.attributes["service.name"] == "test-service"
        assert span.attributes["environment"] == "testing"

        # Test attribute updates
        span.attributes["version"] = "1.0"
        assert span.attributes["version"] == "1.0"

        # Test event addition
        span.add_event("start-process")
        span.add_event("end-process")
        assert len(span.events) == 2

        # Test status management
        span.set_status("ok", "Operation completed successfully")
        assert span.status == "ok"


@pytest.mark.asyncio
async def test_trace_correlation(tracing_manager: TracingManager, test_baggage: dict):
    """Test trace correlation across spans."""
    async with tracing_manager.span("root") as root:
        root.context.baggage.update(test_baggage)

        async with (
            tracing_manager.span("child-1") as child1,
            tracing_manager.span("child-2") as child2,
        ):
            # Test trace correlation
            assert child1.context.trace_id == root.context.trace_id
            assert child2.context.trace_id == root.context.trace_id
            assert child1.context.parent_id == root.context.span_id
            assert child2.context.parent_id == root.context.span_id

            # Test baggage propagation
            assert child1.context.baggage == test_baggage
            assert child2.context.baggage == test_baggage


@pytest.mark.asyncio
async def test_concurrent_spans(tracing_manager: TracingManager):
    """Test concurrent span handling."""

    async def create_child_span(parent_span, name: str, delay: float):
        async with tracing_manager.span(name) as child:
            assert child.context.parent_id == parent_span.context.span_id
            await asyncio.sleep(delay)
            child.add_event(f"{name}-complete")
            return child

    async with tracing_manager.span("parent") as parent:
        # Create multiple concurrent child spans
        children = await asyncio.gather(
            create_child_span(parent, "child-1", 0.1),
            create_child_span(parent, "child-2", 0.2),
            create_child_span(parent, "child-3", 0.3),
        )

        # Verify all children completed
        for child in children:
            assert child.end_time is not None
            assert f"{child.name}-complete" in [event for event in child.events]


@pytest.mark.asyncio
async def test_cleanup(tracing_manager: TracingManager):
    """Test tracing manager cleanup."""
    async with tracing_manager.span("span-1"):
        async with tracing_manager.span("span-2"):
            pass

    await tracing_manager.cleanup()

    async with tracing_manager.span("new-span") as new_span:
        assert new_span.context.trace_id is not None
        assert new_span.context.parent_id is None


@pytest.mark.asyncio
async def test_span_error_handling(tracing_manager: TracingManager):
    """Test span error handling."""
    async with tracing_manager.span("error-span") as span:
        try:
            raise RuntimeError("Test error")
        except Exception as e:
            span.set_status("error", str(e))
            span.add_event("error")
            span.attributes["error.type"] = e.__class__.__name__
            span.attributes["error.message"] = str(e)

        assert span.status == "error"
        assert "error" in [event for event in span.events]
        assert span.attributes["error.type"] == "RuntimeError"


@pytest.mark.asyncio
async def test_nested_spans(tracing_manager: TracingManager):
    """Test deeply nested spans."""
    async with tracing_manager.span("level-1") as span1:
        async with tracing_manager.span("level-2") as span2:
            async with tracing_manager.span("level-3") as span3:
                # Test span hierarchy
                assert span3.context.parent_id == span2.context.span_id
                assert span2.context.parent_id == span1.context.span_id
                assert span1.context.parent_id is None

                # Test trace correlation
                assert span2.context.trace_id == span1.context.trace_id
                assert span3.context.trace_id == span1.context.trace_id

                # Add events at each level
                span1.add_event("level-1-event")
                span2.add_event("level-2-event")
                span3.add_event("level-3-event")


@pytest.mark.asyncio
async def test_span_sampling(tracing_manager: TracingManager):
    """Test span sampling behavior."""
    # Create sampled span
    async with tracing_manager.span("sampled") as sampled_span:
        sampled_span.attributes["sampled"] = "true"
        assert sampled_span.attributes["sampled"] == "true"

    # Create unsampled span
    async with tracing_manager.span("not-sampled") as unsampled_span:
        unsampled_span.attributes["sampled"] = "false"
        assert unsampled_span.attributes["sampled"] == "false"


@pytest.mark.asyncio
async def test_span_events_with_timestamps(tracing_manager: TracingManager):
    """Test span event timing and attributes."""
    async with tracing_manager.span("event-test") as span:
        # Add events with timestamps
        start_time = datetime.utcnow()
        span.add_event("start", start_time)

        await asyncio.sleep(0.1)
        mid_time = datetime.utcnow()
        span.add_event("middle", mid_time)

        await asyncio.sleep(0.1)
        end_time = datetime.utcnow()
        span.add_event("end", end_time)

        # Verify events are in order
        events = [event for event in span.events]
        assert len(events) == 3
        assert events[0] <= events[1] <= events[2]
