"""In-memory store tests."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import pytest

from pepperpy.memory.stores.inmemory import InMemoryStore
from pepperpy.memory.types import (
    MemoryEntry,
    MemoryIndex,
    MemoryQuery,
    MemoryResult,
    MemoryScope,
    MemoryType,
)


@pytest.fixture
def test_entry() -> Dict[str, Any]:
    """Create a test memory entry."""
    return {
        "key": "test1",
        "value": {"content": "test content"},
        "type": MemoryType.SHORT_TERM,
        "scope": MemoryScope.SESSION,
        "metadata": {"tags": "test"},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "expires_at": None,
        "indices": set(),
    }


@pytest.fixture
def store() -> InMemoryStore:
    """Create a test in-memory store."""
    return InMemoryStore(config={})


@pytest.mark.asyncio
async def test_store_initialization(store: InMemoryStore) -> None:
    """Test store initialization."""
    await store.initialize()
    assert store._entries == {}


@pytest.mark.asyncio
async def test_store_cleanup(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test store cleanup."""
    # Add test entry
    entry = MemoryEntry[dict[str, Any]](**test_entry)
    await store.store(entry)

    await store.cleanup()
    assert store._entries == {}


@pytest.mark.asyncio
async def test_store_get(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test getting entries."""
    # Add test entry
    entry = MemoryEntry[dict[str, Any]](**test_entry)
    await store.store(entry)

    # Test getting existing entry
    query = MemoryQuery(query="test1", key="test1")
    async for result in store.retrieve(query):
        assert result.entry.key == "test1"
        assert result.entry.value["content"] == "test content"

    # Test getting non-existent entry
    query = MemoryQuery(query="non_existent", key="non_existent")
    async for result in store.retrieve(query):
        assert False, "Should not find non-existent entry"


@pytest.mark.asyncio
async def test_store_store(store: InMemoryStore) -> None:
    """Test storing entries."""
    # Test storing new entry
    entry = MemoryEntry[dict[str, Any]](
        key="test1",
        value={"content": "test content"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"tags": "test"},
    )
    await store.store(entry)
    assert "test1" in store._entries

    # Test updating existing entry
    updated = MemoryEntry[dict[str, Any]](
        key="test1",
        value={"content": "updated content"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"tags": "test"},
    )
    await store.store(updated)
    assert store._entries["test1"].value["content"] == "updated content"


@pytest.mark.asyncio
async def test_store_delete(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test deleting entries."""
    # Add test entry
    entry = MemoryEntry[dict[str, Any]](**test_entry)
    await store.store(entry)

    # Test deleting existing entry
    result = await store.delete("test1")
    assert result is True
    assert "test1" not in store._entries

    # Test deleting non-existent entry
    result = await store.delete("non_existent")
    assert result is False


@pytest.mark.asyncio
async def test_store_exists(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test checking entry existence."""
    # Add test entry
    entry = MemoryEntry[dict[str, Any]](**test_entry)
    await store.store(entry)

    # Test existing entry
    assert await store.exists("test1") is True

    # Test non-existent entry
    assert await store.exists("non_existent") is False


@pytest.mark.asyncio
async def test_store_clear(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test clearing entries."""
    # Add test entries with different scopes
    entries = {
        "test1": MemoryEntry[dict[str, Any]](**{
            **test_entry,
            "scope": MemoryScope.SESSION,
            "metadata": {"tags": "test"},
        }),
        "test2": MemoryEntry[dict[str, Any]](**{
            **test_entry,
            "key": "test2",
            "scope": MemoryScope.AGENT,
            "metadata": {"tags": "test"},
        }),
    }
    for entry in entries.values():
        await store.store(entry)

    # Test clearing all entries
    count = await store.clear()
    assert count == 2
    assert store._entries == {}

    # Test clearing with scope filter
    for entry in entries.values():
        await store.store(entry)
    count = await store.clear(scope=MemoryScope.SESSION)
    assert count == 1
    assert "test2" in store._entries


@pytest.mark.asyncio
async def test_store_search(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test search functionality."""
    # Add test entries
    entries = {
        "test1": MemoryEntry[dict[str, Any]](**{
            **test_entry,
            "value": {"content": "This is a test document"},
            "metadata": {"tags": "test"},
        }),
        "test2": MemoryEntry[dict[str, Any]](**{
            **test_entry,
            "key": "test2",
            "value": {"content": "Another test document"},
            "metadata": {"tags": "test"},
        }),
        "test3": MemoryEntry[dict[str, Any]](**{
            **test_entry,
            "key": "test3",
            "value": {"content": "Completely different content"},
            "metadata": {"tags": "test"},
        }),
    }
    for entry in entries.values():
        await store.store(entry)

    # Test basic search
    query = MemoryQuery(
        query="test",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.search(query):
        results.append(result)

    assert len(results) > 0
    assert results[0].entry.key == "test1"

    # Test search with filters
    query = MemoryQuery(
        query="test",
        index_type=MemoryIndex.SEMANTIC,
        filters={"type": MemoryType.SHORT_TERM},
        metadata={},
    )
    results = []
    async for result in store.search(query):
        results.append(result)
    assert all(r.entry.type == MemoryType.SHORT_TERM for r in results)


@pytest.mark.asyncio
async def test_store_concurrent_access(store: InMemoryStore) -> None:
    """Test concurrent access to the store."""

    async def write_entry(key: str, content: str) -> None:
        entry = MemoryEntry[dict[str, Any]](
            key=key,
            value={"content": content},
            type=MemoryType.SHORT_TERM,
            scope=MemoryScope.SESSION,
            metadata={"tags": "test"},
        )
        await store.store(entry)

    async def search_entries(query: str) -> List[MemoryResult[dict[str, Any]]]:
        results = []
        async for result in store.search(
            MemoryQuery(
                query=query,
                index_type=MemoryIndex.SEMANTIC,
                filters={},
                metadata={},
            )
        ):
            results.append(result)
        return results

    # Test concurrent writes
    await asyncio.gather(*[write_entry(f"key{i}", f"content{i}") for i in range(10)])
    assert len(store._entries) == 10

    # Test concurrent searches
    results = await asyncio.gather(*[search_entries("test") for _ in range(5)])
    assert len(results) == 5
    assert all(isinstance(r, list) for r in results)
