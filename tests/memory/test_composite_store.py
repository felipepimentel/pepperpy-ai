"""Tests for composite memory store."""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest

from pepperpy.memory.base import MemoryEntry, MemorySearchResult
from pepperpy.memory.config import MemoryConfig
from pepperpy.memory.stores.composite import CompositeMemoryStore
from pepperpy.memory.types import MemoryQuery, MemoryScope, MemoryType


@pytest.fixture
def test_entry() -> Dict[str, Any]:
    """Create a test memory entry."""
    return {
        "key": "test1",
        "value": {"content": "test content"},
        "type": MemoryType.SHORT_TERM.value,
        "scope": MemoryScope.SESSION.value,
        "metadata": {"tags": ["test"]},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "expires_at": None,
        "indices": set(),
    }


@pytest.fixture
def mock_primary_store():
    """Create a mock primary store."""
    store = AsyncMock()
    store.initialize = AsyncMock()
    store.cleanup = AsyncMock()
    store.store = AsyncMock()
    store.get = AsyncMock()
    store.delete = AsyncMock()
    store.exists = AsyncMock()
    store.clear = AsyncMock()
    store.search = AsyncMock()
    store._retrieve = AsyncMock()
    return store


@pytest.fixture
def mock_secondary_store():
    """Create a mock secondary store."""
    store = AsyncMock()
    store.initialize = AsyncMock()
    store.cleanup = AsyncMock()
    store.store = AsyncMock()
    store.get = AsyncMock()
    store.delete = AsyncMock()
    store.exists = AsyncMock()
    store.clear = AsyncMock()
    store.search = AsyncMock()
    store._retrieve = AsyncMock()
    return store


@pytest.fixture
def store(mock_primary_store):
    """Create a test composite store."""
    return CompositeMemoryStore(
        config=MemoryConfig(),
        primary_store=mock_primary_store,
    )


@pytest.mark.asyncio
async def test_store_initialization(store, mock_primary_store):
    """Test store initialization."""
    await store.initialize()
    assert mock_primary_store.initialize.called


@pytest.mark.asyncio
async def test_store_cleanup(store, mock_primary_store):
    """Test store cleanup."""
    await store.cleanup()
    assert mock_primary_store.cleanup.called


@pytest.mark.asyncio
async def test_store_get(store, mock_primary_store, test_entry):
    """Test getting entries."""
    # Mock entry retrieval
    mock_primary_store.get.return_value = MemoryEntry[Dict[str, Any]](**test_entry)

    # Test getting existing entry
    result = await store.get("test1")
    assert result is not None
    assert result.key == "test1"
    assert result.value["content"] == "test content"
    assert mock_primary_store.get.called

    # Test getting non-existent entry
    mock_primary_store.get.return_value = None
    result = await store.get("non_existent")
    assert result is None


@pytest.mark.asyncio
async def test_store_set(store, mock_primary_store):
    """Test setting entries."""
    # Test setting new entry
    entry = await store.set(
        "test1",
        {"content": "test content"},
        scope=MemoryScope.SESSION.value,
        metadata={"tags": ["test"]},
    )
    assert entry.key == "test1"
    assert entry.value["content"] == "test content"
    assert entry.scope == MemoryScope.SESSION.value
    assert entry.metadata == {"tags": ["test"]}
    assert mock_primary_store.store.called

    # Test updating existing entry
    updated = await store.set(
        "test1",
        {"content": "updated content"},
        scope=MemoryScope.SESSION.value,
    )
    assert updated.value["content"] == "updated content"
    assert mock_primary_store.store.call_count == 2


@pytest.mark.asyncio
async def test_store_delete(store, mock_primary_store):
    """Test deleting entries."""
    # Test deleting existing entry
    mock_primary_store.delete.return_value = True
    result = await store.delete("test1")
    assert result is True
    assert mock_primary_store.delete.called

    # Test deleting non-existent entry
    mock_primary_store.delete.return_value = False
    result = await store.delete("non_existent")
    assert result is False


@pytest.mark.asyncio
async def test_store_exists(store, mock_primary_store):
    """Test checking entry existence."""
    # Test existing entry
    mock_primary_store.exists.return_value = True
    assert await store.exists("test1") is True
    assert mock_primary_store.exists.called

    # Test non-existent entry
    mock_primary_store.exists.return_value = False
    assert await store.exists("non_existent") is False


@pytest.mark.asyncio
async def test_store_clear(store, mock_primary_store):
    """Test clearing entries."""
    # Test clearing all entries
    mock_primary_store.clear.return_value = 2
    count = await store.clear()
    assert count == 2
    assert mock_primary_store.clear.called

    # Test clearing with scope filter
    mock_primary_store.clear.return_value = 1
    count = await store.clear(scope=MemoryScope.SESSION.value)
    assert count == 1
    assert mock_primary_store.clear.called


@pytest.mark.asyncio
async def test_store_search(store, mock_primary_store, test_entry):
    """Test search functionality."""
    # Mock search results
    results_iter = [
        MemorySearchResult[Dict[str, Any]](
            entry=MemoryEntry[Dict[str, Any]](**test_entry),
            score=1.0,
        ),
    ]
    mock_primary_store._retrieve.return_value = AsyncMock(
        __aiter__=lambda: iter(results_iter)
    )()

    # Test basic search
    results = []
    async for result in store.search(MemoryQuery(query="test")):
        results.append(result)

    assert len(results) > 0
    assert results[0].entry.key == "test1"
    assert mock_primary_store._retrieve.called

    # Test search with filters
    results_iter = [
        MemorySearchResult[Dict[str, Any]](
            entry=MemoryEntry[Dict[str, Any]](**test_entry),
            score=1.0,
        ),
    ]
    mock_primary_store._retrieve.return_value = AsyncMock(
        __aiter__=lambda: iter(results_iter)
    )()

    results = []
    async for result in store.search(
        MemoryQuery(
            query="test",
            filters={"type": MemoryType.SHORT_TERM.value},
        )
    ):
        results.append(result)
    assert all(r.entry.type == MemoryType.SHORT_TERM.value for r in results)


@pytest.mark.asyncio
async def test_store_concurrent_access(store, mock_primary_store):
    """Test concurrent access to the store."""

    async def write_entry(key: str, content: str) -> None:
        await store.set(key, {"content": content})

    async def search_entries(query: str) -> list:
        results = []
        async for result in store.search(MemoryQuery(query=query)):
            results.append(result)
        return results

    # Mock search results for concurrent searches
    results_iter = [
        MemorySearchResult[Dict[str, Any]](
            entry=MemoryEntry[Dict[str, Any]](**test_entry()),
            score=1.0,
        ),
    ]
    mock_primary_store._retrieve.return_value = AsyncMock(
        __aiter__=lambda: iter(results_iter)
    )()

    # Test concurrent writes
    await asyncio.gather(*[write_entry(f"key{i}", f"content{i}") for i in range(10)])
    assert mock_primary_store.store.call_count == 10

    # Test concurrent searches
    results = await asyncio.gather(*[search_entries("test") for _ in range(5)])
    assert len(results) == 5
    assert all(isinstance(r, list) for r in results)


@pytest.mark.asyncio
async def test_store_add_secondary(store, mock_primary_store, mock_secondary_store):
    """Test adding secondary store."""
    # Add secondary store
    await store.add_store(mock_secondary_store)
    assert len(store._stores) == 2

    # Test that operations are propagated to both stores
    entry = await store.set(
        "test1",
        {"content": "test content"},
        scope=MemoryScope.SESSION.value,
    )
    assert mock_primary_store.store.called
    assert mock_secondary_store.store.called

    # Test that secondary store errors are handled gracefully
    mock_secondary_store.store.side_effect = Exception("Secondary store error")
    entry = await store.set(
        "test2",
        {"content": "test content"},
        scope=MemoryScope.SESSION.value,
    )
    assert mock_primary_store.store.call_count == 2  # Still stored in primary


@pytest.mark.asyncio
async def test_store_error_handling(store, mock_primary_store):
    """Test error handling in composite store."""
    # Test primary store error
    mock_primary_store.store.side_effect = Exception("Primary store error")
    with pytest.raises(RuntimeError):
        await store.set(
            "test1",
            {"content": "test content"},
            scope=MemoryScope.SESSION.value,
        )
