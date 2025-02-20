"""Memory store tests."""

from typing import Any

import pytest

from pepperpy.memory.store import BaseMemoryStore
from pepperpy.memory.stores.memory import InMemoryStore
from pepperpy.memory.types import (
    MemoryEntry,
    MemoryIndex,
    MemoryQuery,
    MemoryResult,
    MemoryScope,
)


@pytest.fixture
def store() -> BaseMemoryStore[dict[str, Any]]:
    """Create test store."""
    return InMemoryStore(config={})


@pytest.mark.asyncio
async def test_memory_store_operations(store: BaseMemoryStore[dict[str, Any]]) -> None:
    """Test memory store operations."""
    # Test storing an entry
    entry = await store.store(
        key="test1",
        content={"data": "test data"},
        scope=MemoryScope.SESSION,
        metadata={"test": "true"},
    )
    assert isinstance(entry, MemoryEntry)
    assert entry.key == "test1"
    assert entry.value["data"] == "test data"

    # Test retrieving the entry
    query = MemoryQuery(
        query="test1",
        key="test1",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert isinstance(results[0], MemoryResult)
    assert results[0].key == entry.key
    assert results[0].entry["data"] == "test data"

    # Test updating an entry
    updated_entry = await store.store(
        key="test1",
        content={"data": "updated data"},
        scope=MemoryScope.SESSION,
        metadata={"test": "true", "updated": "true"},
    )
    assert isinstance(updated_entry, MemoryEntry)
    assert updated_entry.key == "test1"
    assert updated_entry.value["data"] == "updated data"

    # Test retrieving the updated entry
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert isinstance(results[0], MemoryResult)
    assert results[0].key == updated_entry.key
    assert results[0].entry["data"] == "updated data"
    assert results[0].metadata["updated"] == "true"

    # Test deleting the entry
    deleted = await store.delete("test1")
    assert deleted

    # Verify entry is deleted
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_memory_store_search(store: BaseMemoryStore[dict[str, Any]]) -> None:
    """Test memory store search."""
    # Store multiple entries
    entry1 = await store.store(
        key="user1",
        content={
            "name": "John Doe",
            "email": "john@example.com",
            "tags": ["user", "admin"],
        },
        scope=MemoryScope.GLOBAL,
        metadata={"source": "test"},
    )
    assert isinstance(entry1, MemoryEntry)

    entry2 = await store.store(
        key="user2",
        content={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "tags": ["user"],
        },
        scope=MemoryScope.GLOBAL,
        metadata={"source": "test"},
    )
    assert isinstance(entry2, MemoryEntry)

    # Test basic search
    query = MemoryQuery(
        query="john",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert isinstance(results[0], MemoryResult)
    assert results[0].key == entry1.key

    # Test search with multiple results
    query = MemoryQuery(
        query="user",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 2
    assert all(isinstance(r, MemoryResult) for r in results)

    # Test search with metadata
    query = MemoryQuery(
        query="test",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={"source": "test"},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 2
    assert all(isinstance(r, MemoryResult) for r in results)

    # Test empty query
    query = MemoryQuery(
        query="",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_memory_store_error_handling(
    store: BaseMemoryStore[dict[str, Any]],
) -> None:
    """Test memory store error handling."""
    # Test storing with invalid key
    with pytest.raises(ValueError):
        await store.store(
            key="",
            content={"data": "test data"},
            scope=MemoryScope.SESSION,
            metadata=None,
        )

    # Test storing with invalid content
    with pytest.raises(ValueError):
        await store.store(
            key="test2", content={}, scope=MemoryScope.SESSION, metadata=None
        )

    # Test empty query
    query = MemoryQuery(
        query="",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 0
