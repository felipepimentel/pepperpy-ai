"""Test fixtures for tracing testing."""

from typing import AsyncGenerator, Dict

import pytest

from pepperpy.core.monitoring.tracing import SpanContext, TracingManager


@pytest.fixture
async def tracing_manager() -> AsyncGenerator[TracingManager, None]:
    """Provide a tracing manager instance."""
    manager = TracingManager()
    yield manager
    await manager.cleanup()


@pytest.fixture
def test_context() -> SpanContext:
    """Provide a test span context."""
    return SpanContext(
        trace_id="test-trace-1",
        span_id="test-span-1",
        parent_id=None,
        baggage={"app": "test"},
    )


@pytest.fixture
def test_baggage() -> Dict[str, str]:
    """Provide test baggage items."""
    return {
        "app": "test",
        "environment": "testing",
        "version": "1.0",
    }
