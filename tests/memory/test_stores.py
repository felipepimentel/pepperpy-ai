"""Tests for memory store implementations."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest

from pepperpy.memory.stores.inmemory import InMemoryStore
from pepperpy.memory.types import MemoryEntry, MemoryQuery, MemoryScope, MemoryType


@pytest.fixture
def store():
    """Create a test memory store."""
    return InMemoryStore({})


@pytest.fixture
def test_entry() -> Dict[str, Any]:
    """Create a test memory entry."""
    return {
        "key": "test1",
        "value": {"content": "test content"},
        "type": MemoryType.SHORT_TERM,
        "scope": MemoryScope.SESSION,
        "metadata": {"tags": ["test"]},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "expires_at": None,
        "indices": set(),
    }


@pytest.mark.asyncio
async def test_store_initialization(store):
    """Test store initialization."""
    await store.initialize()
    assert store._entries == {}


@pytest.mark.asyncio
async def test_store_cleanup(store):
    """Test store cleanup."""
    # Add some test entries
    entry = MemoryEntry(**test_entry())
    async with store._lock:
        store._entries["test1"] = entry

    await store.cleanup()
    assert store._entries == {}


@pytest.mark.asyncio
async def test_store_get(store):
    """Test getting entries."""
    # Add test entry
    entry = MemoryEntry(**test_entry())
    async with store._lock:
        store._entries["test1"] = entry

    # Test getting existing entry
    result = await store.get("test1")
    assert result is not None
    assert result.key == "test1"
    assert result.value["content"] == "test content"

    # Test getting non-existent entry
    result = await store.get("non_existent")
    assert result is None


@pytest.mark.asyncio
async def test_store_set(store):
    """Test setting entries."""
    # Test setting new entry
    entry = await store.set(
        "test1",
        {"content": "test content"},
        scope=MemoryScope.SESSION,
        metadata={"tags": ["test"]},
    )
    assert entry.key == "test1"
    assert entry.value["content"] == "test content"
    assert entry.scope == MemoryScope.SESSION
    assert entry.metadata == {"tags": ["test"]}

    # Test updating existing entry
    updated = await store.set(
        "test1",
        {"content": "updated content"},
        scope=MemoryScope.SESSION,
    )
    assert updated.value["content"] == "updated content"


@pytest.mark.asyncio
async def test_store_delete(store):
    """Test deleting entries."""
    # Add test entry
    entry = MemoryEntry(**test_entry())
    async with store._lock:
        store._entries["test1"] = entry

    # Test deleting existing entry
    result = await store.delete("test1")
    assert result is True
    assert "test1" not in store._entries

    # Test deleting non-existent entry
    result = await store.delete("non_existent")
    assert result is False


@pytest.mark.asyncio
async def test_store_exists(store):
    """Test checking entry existence."""
    # Add test entry
    entry = MemoryEntry(**test_entry())
    async with store._lock:
        store._entries["test1"] = entry

    # Test existing entry
    assert await store.exists("test1") is True

    # Test non-existent entry
    assert await store.exists("non_existent") is False


@pytest.mark.asyncio
async def test_store_clear(store):
    """Test clearing entries."""
    # Add test entries with different scopes
    entries = {
        "test1": MemoryEntry(**{
            **test_entry(),
            "scope": MemoryScope.SESSION,
        }),
        "test2": MemoryEntry(**{
            **test_entry(),
            "key": "test2",
            "scope": MemoryScope.AGENT,
        }),
    }
    async with store._lock:
        store._entries.update(entries)

    # Test clearing all entries
    count = await store.clear()
    assert count == 2
    assert store._entries == {}

    # Test clearing with scope filter
    async with store._lock:
        store._entries.update(entries)
    count = await store.clear(scope=MemoryScope.SESSION)
    assert count == 1
    assert "test2" in store._entries


@pytest.mark.asyncio
async def test_store_expiration(store):
    """Test entry expiration handling."""
    # Add expired entry
    expired_entry = MemoryEntry(**{
        **test_entry(),
        "expires_at": datetime.utcnow() - timedelta(hours=1),
    })
    async with store._lock:
        store._entries["expired"] = expired_entry

    # Add non-expired entry
    valid_entry = MemoryEntry(**{
        **test_entry(),
        "key": "valid",
        "expires_at": datetime.utcnow() + timedelta(hours=1),
    })
    async with store._lock:
        store._entries["valid"] = valid_entry

    # Check expiration
    assert store._is_expired(expired_entry, datetime.utcnow()) is True
    assert store._is_expired(valid_entry, datetime.utcnow()) is False


@pytest.mark.asyncio
async def test_store_query_filters(store):
    """Test query filtering."""
    entry = MemoryEntry(**test_entry())

    # Test scope filter
    query = MemoryQuery(
        query="test",
        filters={"scope": MemoryScope.SESSION},
    )
    assert store._matches_filters(entry, query) is True

    query = MemoryQuery(
        query="test",
        filters={"scope": MemoryScope.AGENT},
    )
    assert store._matches_filters(entry, query) is False

    # Test type filter
    query = MemoryQuery(
        query="test",
        filters={"type": MemoryType.SHORT_TERM},
    )
    assert store._matches_filters(entry, query) is True

    query = MemoryQuery(
        query="test",
        filters={"type": MemoryType.LONG_TERM},
    )
    assert store._matches_filters(entry, query) is False

    # Test metadata filter
    query = MemoryQuery(
        query="test",
        metadata={"tags": ["test"]},
    )
    assert store._matches_filters(entry, query) is True

    query = MemoryQuery(
        query="test",
        metadata={"tags": ["non_existent"]},
    )
    assert store._matches_filters(entry, query) is False


@pytest.mark.asyncio
async def test_store_text_search(store):
    """Test text search functionality."""
    entry = MemoryEntry(**test_entry())

    # Test matching text
    assert store._matches_text_search(entry, "test") is True
    assert store._matches_text_search(entry, "content") is True

    # Test non-matching text
    assert store._matches_text_search(entry, "non_existent") is False

    # Test empty query
    assert store._matches_text_search(entry, None) is True
    assert store._matches_text_search(entry, "") is True


@pytest.mark.asyncio
async def test_store_concurrent_access(store):
    """Test concurrent access to the store."""

    async def write_entry(key: str, value: dict) -> None:
        await store.set(key, value)

    async def read_entry(key: str) -> MemoryEntry:
        return await store.get(key)

    # Test concurrent writes
    await asyncio.gather(*[
        write_entry(f"key{i}", {"value": f"value{i}"}) for i in range(10)
    ])
    assert len(store._entries) == 10

    # Test concurrent reads
    results = await asyncio.gather(*[read_entry(f"key{i}") for i in range(10)])
    assert len(results) == 10
    assert all(r is not None for r in results)
    assert all(r.value["value"] == f"value{i}" for i, r in enumerate(results))
