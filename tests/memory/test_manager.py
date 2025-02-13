"""Tests for memory manager."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock

import pytest

from pepperpy.core.errors import ConfigurationError
from pepperpy.memory.base import (
    BaseMemory,
    MemoryEntry,
    MemoryQuery,
    MemoryScope,
    MemorySearchResult,
    MemoryType,
)
from pepperpy.memory.manager import MemoryManager


class MockMemory(BaseMemory[str, dict[str, Any]]):
    """Mock memory implementation for testing."""

    def __init__(self) -> None:
        """Initialize mock memory."""
        self.store = AsyncMock()
        self.retrieve = AsyncMock()
        self.search = AsyncMock()
        self.cleanup_expired = AsyncMock()
        self.initialize = AsyncMock()
        self.cleanup = AsyncMock()
        self.similar = AsyncMock()


@pytest.fixture
def short_term_memory() -> MockMemory:
    """Create mock short-term memory."""
    return MockMemory()


@pytest.fixture
def medium_term_memory() -> MockMemory:
    """Create mock medium-term memory."""
    return MockMemory()


@pytest.fixture
def long_term_memory() -> MockMemory:
    """Create mock long-term memory."""
    return MockMemory()


@pytest.fixture
def memory_manager(
    short_term_memory: MockMemory,
    medium_term_memory: MockMemory,
    long_term_memory: MockMemory,
) -> MemoryManager[str]:
    """Create memory manager with mock memories."""
    return MemoryManager(
        short_term=short_term_memory,
        medium_term=medium_term_memory,
        long_term=long_term_memory,
        cleanup_interval=1,
        reindex_interval=1,
    )


@pytest.mark.asyncio
async def test_memory_manager_init():
    """Test memory manager initialization."""
    # Test with only short-term memory
    short_term = MockMemory()
    manager = MemoryManager(short_term=short_term)
    assert manager._memories[MemoryType.SHORT_TERM] == short_term
    assert MemoryType.MEDIUM_TERM not in manager._memories
    assert MemoryType.LONG_TERM not in manager._memories

    # Test with all memory types
    medium_term = MockMemory()
    long_term = MockMemory()
    manager = MemoryManager(
        short_term=short_term,
        medium_term=medium_term,
        long_term=long_term,
    )
    assert manager._memories[MemoryType.SHORT_TERM] == short_term
    assert manager._memories[MemoryType.MEDIUM_TERM] == medium_term
    assert manager._memories[MemoryType.LONG_TERM] == long_term


@pytest.mark.asyncio
async def test_memory_manager_start_stop(memory_manager: MemoryManager[str]):
    """Test memory manager start and stop."""
    # Test start
    await memory_manager.start()
    assert memory_manager.is_active
    assert memory_manager._cleanup_task is not None

    # Test start when already active
    with pytest.raises(RuntimeError, match="Memory manager is already active"):
        await memory_manager.start()

    # Test stop
    await memory_manager.stop()
    assert not memory_manager.is_active
    assert memory_manager._cleanup_task is None


@pytest.mark.asyncio
async def test_memory_manager_cleanup_loop(
    memory_manager: MemoryManager[str],
    short_term_memory: MockMemory,
    medium_term_memory: MockMemory,
    long_term_memory: MockMemory,
):
    """Test memory cleanup loop."""
    # Set up cleanup results
    short_term_memory.cleanup_expired.return_value = 1
    medium_term_memory.cleanup_expired.return_value = 2
    long_term_memory.cleanup_expired.return_value = 3

    # Start manager and wait for one cleanup cycle
    await memory_manager.start()
    await asyncio.sleep(1.1)  # Wait slightly longer than cleanup interval
    await memory_manager.stop()

    # Verify cleanup was called for each memory
    assert short_term_memory.cleanup_expired.called
    assert medium_term_memory.cleanup_expired.called
    assert long_term_memory.cleanup_expired.called


@pytest.mark.asyncio
async def test_memory_manager_store(
    memory_manager: MemoryManager[str], short_term_memory: MockMemory
):
    """Test storing memory entries."""
    # Set up mock return value
    entry = MemoryEntry(
        key="test",
        value={"data": "test"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        created_at=datetime.utcnow(),
    )
    short_term_memory.store.return_value = entry

    # Test store with defaults
    result = await memory_manager.store("test", {"data": "test"})
    assert result == entry
    short_term_memory.store.assert_called_once()

    # Test store with expiration
    expires_in = timedelta(hours=1)
    await memory_manager.store("test", {"data": "test"}, expires_in=expires_in)
    assert short_term_memory.store.call_args[1]["expires_at"] is not None

    # Test store with invalid memory type
    with pytest.raises(ConfigurationError, match="Memory type not configured"):
        await memory_manager.store(
            "test",
            {"data": "test"},
            type=MemoryType.WORKING,  # type: ignore
        )


@pytest.mark.asyncio
async def test_memory_manager_retrieve(
    memory_manager: MemoryManager[str],
    short_term_memory: MockMemory,
    medium_term_memory: MockMemory,
    long_term_memory: MockMemory,
):
    """Test retrieving memory entries."""
    # Set up mock return value
    entry = MemoryEntry(
        key="test",
        value={"data": "test"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        created_at=datetime.utcnow(),
    )
    short_term_memory.retrieve.return_value = entry

    # Test retrieve with specific type
    result = await memory_manager.retrieve("test", type=MemoryType.SHORT_TERM)
    assert result == entry
    short_term_memory.retrieve.assert_called_once()

    # Test retrieve without type (should try all memories)
    short_term_memory.retrieve.reset_mock()
    short_term_memory.retrieve.side_effect = KeyError()
    medium_term_memory.retrieve.side_effect = KeyError()
    long_term_memory.retrieve.return_value = entry

    result = await memory_manager.retrieve("test")
    assert result == entry
    assert short_term_memory.retrieve.called
    assert medium_term_memory.retrieve.called
    assert long_term_memory.retrieve.called

    # Test retrieve with key not found
    short_term_memory.retrieve.reset_mock()
    medium_term_memory.retrieve.reset_mock()
    long_term_memory.retrieve.reset_mock()
    short_term_memory.retrieve.side_effect = KeyError()
    medium_term_memory.retrieve.side_effect = KeyError()
    long_term_memory.retrieve.side_effect = KeyError()

    with pytest.raises(KeyError, match="Memory key not found"):
        await memory_manager.retrieve("test")


@pytest.mark.asyncio
async def test_memory_manager_search(
    memory_manager: MemoryManager[str],
    short_term_memory: MockMemory,
    medium_term_memory: MockMemory,
    long_term_memory: MockMemory,
):
    """Test searching memory entries."""

    # Set up mock return values
    async def mock_search_results() -> AsyncIterator[
        MemorySearchResult[dict[str, Any]]
    ]:
        yield MemorySearchResult(
            entry=MemoryEntry(
                key="test",
                value={"data": "test"},
                type=MemoryType.SHORT_TERM,
                scope=MemoryScope.SESSION,
                created_at=datetime.utcnow(),
            ),
            score=1.0,
        )

    short_term_memory.search.return_value = mock_search_results()
    query = MemoryQuery(query="test")

    # Test search with specific type
    results = []
    async for result in memory_manager.search(query, type=MemoryType.SHORT_TERM):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == "test"
    short_term_memory.search.assert_called_once()

    # Test search without type (should try all memories)
    short_term_memory.search.reset_mock()
    medium_term_memory.search.return_value = mock_search_results()
    long_term_memory.search.return_value = mock_search_results()

    results = []
    async for result in memory_manager.search(query):
        results.append(result)
    assert len(results) == 3  # One from each memory type
    assert short_term_memory.search.called
    assert medium_term_memory.search.called
    assert long_term_memory.search.called
