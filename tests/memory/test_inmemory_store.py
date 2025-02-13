"""Tests for in-memory store."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest

from pepperpy.memory.base import MemoryEntry
from pepperpy.memory.stores.inmemory import InMemoryStore
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
def store():
    """Create a test in-memory store."""
    return InMemoryStore()


@pytest.mark.asyncio
async def test_store_initialization(store):
    """Test store initialization."""
    await store.initialize()
    assert store._entries == {}


@pytest.mark.asyncio
async def test_store_cleanup(store, test_entry):
    """Test store cleanup."""
    # Add test entry
    entry = MemoryEntry[Dict[str, Any]](**test_entry)
    async with store._lock:
        store._entries["test1"] = entry

    await store.cleanup()
    assert store._entries == {}


@pytest.mark.asyncio
async def test_store_get(store, test_entry):
    """Test getting entries."""
    # Add test entry
    entry = MemoryEntry[Dict[str, Any]](**test_entry)
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
        scope=MemoryScope.SESSION.value,
        metadata={"tags": ["test"]},
    )
    assert entry.key == "test1"
    assert entry.value["content"] == "test content"
    assert entry.scope == MemoryScope.SESSION.value
    assert entry.metadata == {"tags": ["test"]}
    assert "test1" in store._entries

    # Test updating existing entry
    updated = await store.set(
        "test1",
        {"content": "updated content"},
        scope=MemoryScope.SESSION.value,
    )
    assert updated.value["content"] == "updated content"
    assert "test1" in store._entries


@pytest.mark.asyncio
async def test_store_delete(store, test_entry):
    """Test deleting entries."""
    # Add test entry
    entry = MemoryEntry[Dict[str, Any]](**test_entry)
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
async def test_store_exists(store, test_entry):
    """Test checking entry existence."""
    # Add test entry
    entry = MemoryEntry[Dict[str, Any]](**test_entry)
    async with store._lock:
        store._entries["test1"] = entry

    # Test existing entry
    assert await store.exists("test1") is True

    # Test non-existent entry
    assert await store.exists("non_existent") is False


@pytest.mark.asyncio
async def test_store_clear(store, test_entry):
    """Test clearing entries."""
    # Add test entries with different scopes
    entries = {
        "test1": MemoryEntry[Dict[str, Any]](**{
            **test_entry,
            "scope": MemoryScope.SESSION.value,
        }),
        "test2": MemoryEntry[Dict[str, Any]](**{
            **test_entry,
            "key": "test2",
            "scope": MemoryScope.AGENT.value,
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
    count = await store.clear(scope=MemoryScope.SESSION.value)
    assert count == 1
    assert "test2" in store._entries


@pytest.mark.asyncio
async def test_store_expiration(store):
    """Test entry expiration handling."""
    # Add expired entry
    expired_entry = MemoryEntry[Dict[str, Any]](**{
        **test_entry(),
        "expires_at": datetime.utcnow() - timedelta(hours=1),
    })
    async with store._lock:
        store._entries["expired"] = expired_entry

    # Add non-expired entry
    valid_entry = MemoryEntry[Dict[str, Any]](**{
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
async def test_store_search(store, test_entry):
    """Test search functionality."""
    # Add test entries
    entries = {
        "test1": MemoryEntry[Dict[str, Any]](**{
            **test_entry,
            "value": {"content": "This is a test document"},
        }),
        "test2": MemoryEntry[Dict[str, Any]](**{
            **test_entry,
            "key": "test2",
            "value": {"content": "Another test document"},
        }),
        "test3": MemoryEntry[Dict[str, Any]](**{
            **test_entry,
            "key": "test3",
            "value": {"content": "Completely different content"},
        }),
    }
    async with store._lock:
        store._entries.update(entries)

    # Test basic search
    results = []
    async for result in store.search(MemoryQuery(query="test")):
        results.append(result)

    assert len(results) > 0
    assert results[0].entry.key == "test1"

    # Test search with filters
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
async def test_store_concurrent_access(store):
    """Test concurrent access to the store."""

    async def write_entry(key: str, content: str) -> None:
        await store.set(key, {"content": content})

    async def search_entries(query: str) -> list:
        results = []
        async for result in store.search(MemoryQuery(query=query)):
            results.append(result)
        return results

    # Test concurrent writes
    await asyncio.gather(*[write_entry(f"key{i}", f"content{i}") for i in range(10)])
    assert len(store._entries) == 10

    # Test concurrent searches
    results = await asyncio.gather(*[search_entries("test") for _ in range(5)])
    assert len(results) == 5
    assert all(isinstance(r, list) for r in results)
