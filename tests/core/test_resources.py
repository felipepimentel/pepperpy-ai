"""Integration tests for resource management system."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Optional

import pytest

from pepperpy.core.errors import LifecycleError, ResourceError
from pepperpy.core.resources import Resource, resource_session
from pepperpy.memory.errors import (
    MemoryError,
    MemoryKeyError,
)
from pepperpy.memory.simple import SimpleMemory


class MockResource(Resource):
    """Mock resource for testing."""

    _mock_initialized: bool
    _mock_cleaned_up: bool
    _mock_cleanup_count: int
    fail_init: bool
    fail_cleanup: bool

    def __init__(
        self,
        auto_cleanup: bool = True,
        cleanup_interval: Optional[int] = None,
        fail_init: bool = False,
        fail_cleanup: bool = False,
    ) -> None:
        """Initialize mock resource.

        Args:
            auto_cleanup: Whether to automatically clean up
            cleanup_interval: Optional cleanup interval
            fail_init: Whether to fail initialization
            fail_cleanup: Whether to fail cleanup
        """
        super().__init__(auto_cleanup=auto_cleanup, cleanup_interval=cleanup_interval)
        self.fail_init = fail_init
        self.fail_cleanup = fail_cleanup
        self._mock_initialized = False
        self._mock_cleaned_up = False
        self._mock_cleanup_count = 0

    async def _initialize(self) -> None:
        """Initialize mock resource."""
        if self.fail_init:
            raise ResourceError("Mock initialization failure")
        self._mock_initialized = True

    async def _cleanup(self) -> None:
        """Clean up mock resource."""
        if self.fail_cleanup:
            raise ResourceError("Mock cleanup failure")
        self._mock_cleaned_up = True
        self._mock_cleanup_count += 1


@pytest.mark.asyncio
async def test_resource_lifecycle():
    """Test basic resource lifecycle."""
    resource = MockResource()

    # Test initialization
    assert not resource._initialized
    await resource.initialize()
    assert resource._initialized
    assert resource._mock_initialized

    # Test cleanup
    await resource.cleanup()
    assert not resource._initialized
    assert resource._mock_cleaned_up
    assert resource._mock_cleanup_count == 1


@pytest.mark.asyncio
async def test_resource_session():
    """Test resource session context manager."""
    resource = MockResource()

    async with resource_session(resource) as r:
        assert r._initialized
        assert r._mock_initialized

    assert not resource._initialized
    assert resource._mock_cleaned_up
    assert resource._mock_cleanup_count == 1


@pytest.mark.asyncio
async def test_auto_cleanup():
    """Test automatic resource cleanup."""
    resource = MockResource(cleanup_interval=1)

    await resource.initialize()
    assert resource._initialized

    # Wait for auto cleanup
    await asyncio.sleep(1.5)
    assert resource._mock_cleanup_count >= 1

    await resource.cleanup()


@pytest.mark.asyncio
async def test_initialization_failure():
    """Test resource initialization failure."""
    resource = MockResource(fail_init=True)

    with pytest.raises(LifecycleError) as exc:
        await resource.initialize()
    assert "Failed to initialize resource" in str(exc.value)
    assert not resource._initialized


@pytest.mark.asyncio
async def test_cleanup_failure():
    """Test resource cleanup failure."""
    resource = MockResource(fail_cleanup=True)

    await resource.initialize()
    with pytest.raises(LifecycleError) as exc:
        await resource.cleanup()
    assert "Failed to clean up resource" in str(exc.value)


@pytest.mark.asyncio
async def test_simple_memory_lifecycle():
    """Test SimpleMemory resource lifecycle."""
    memory = SimpleMemory(cleanup_interval=1)

    # Test initialization
    await memory.initialize()
    assert memory._initialized

    # Store and retrieve values
    await memory.store("key1", "value1")
    assert await memory.retrieve("key1") == "value1"

    # Test expiration
    await memory.store(
        "key2",
        "value2",
        expires_at=datetime.now(UTC) + timedelta(seconds=1),
    )
    assert await memory.retrieve("key2") == "value2"

    # Wait for expiration and auto cleanup
    await asyncio.sleep(1.5)
    with pytest.raises(MemoryKeyError):
        await memory.retrieve("key2")

    # Test cleanup
    await memory.cleanup()
    assert not memory._initialized

    # Test operations on uninitialized memory
    with pytest.raises(MemoryError):
        await memory.store("key3", "value3")
    with pytest.raises(MemoryError):
        await memory.retrieve("key3")
