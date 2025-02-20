"""Tests for memory store functionality."""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from pepperpy.memory import (
    MemoryEntry,
    MemoryIndex,
    MemoryQuery,
    MemoryScope,
    MemoryStoreType,
    MemoryType,
    create_memory_store,
)


@pytest.mark.asyncio
async def test_memory_store_creation() -> None:
    """Test memory store creation."""
    store = create_memory_store(MemoryStoreType.MEMORY)
    assert store is not None


@pytest.mark.asyncio
async def test_memory_store_operations() -> None:
    """Test memory store operations."""
    store = create_memory_store(MemoryStoreType.MEMORY)

    # Test storing an entry
    entry = MemoryEntry[Dict[str, Any]](
        key="test1",
        value={"data": "test data"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"test": True},
        expires_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    await store._store(entry)

    # Test retrieving an entry
    query = MemoryQuery(
        query="test1",
        key="test1",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == "test1"
    assert results[0].entry.value == {"data": "test data"}

    # Test retrieving a non-existent entry
    query = MemoryQuery(
        query="non_existent",
        key="non_existent",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_composite_memory_store() -> None:
    """Test composite memory store."""
    # Create stores
    store1 = create_memory_store(MemoryStoreType.MEMORY)
    store2 = create_memory_store(MemoryStoreType.MEMORY)
    composite = create_memory_store(
        MemoryStoreType.COMPOSITE,
        stores=[store1, store2],
    )

    # Store entries in different stores
    entry1 = MemoryEntry[Dict[str, Any]](
        key="test1",
        value={"data": "test1"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"store": "store1"},
        created_at=datetime.now(timezone.utc),
    )
    await store1._store(entry1)

    entry2 = MemoryEntry[Dict[str, Any]](
        key="test2",
        value={"data": "test2"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"store": "store2"},
        created_at=datetime.now(timezone.utc),
    )
    await store2._store(entry2)

    entry3 = MemoryEntry[Dict[str, Any]](
        key="test3",
        value={"data": "test3"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"store": "composite"},
        created_at=datetime.now(timezone.utc),
    )
    await composite._store(entry3)

    # Test retrieving entries
    query = MemoryQuery(
        query="test1",
        key="test1",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in composite._retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.metadata["store"] == "store1"

    query = MemoryQuery(
        query="test2",
        key="test2",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in composite._retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.metadata["store"] == "store2"

    # Test searching across stores
    query = MemoryQuery(
        query="test",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in composite._retrieve(query):
        results.append(result)
    assert len(results) == 3
