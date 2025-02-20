"""In-memory store tests."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Dict

import pytest

from pepperpy.memory import (
    MemoryError,
    MemoryKeyError,
    MemoryQuery,
    MemoryStoreType,
    MemoryType,
    create_memory_store,
)
from pepperpy.memory.base import MemoryEntry, MemoryIndex


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
        metadata={"test": True},
        created_at=datetime.now(UTC),
    )
    await store._store(entry)
    assert entry.key == "test1"
    assert entry.value == {"data": "test data"}
    assert entry.type == MemoryType.SHORT_TERM
    assert entry.metadata == {"test": True}
    assert entry.created_at is not None

    # Test retrieving an entry
    query = MemoryQuery(
        query="test1",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry == entry

    # Test retrieving a non-existent entry
    query = MemoryQuery(
        query="non_existent",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 0

    # Test storing with invalid key
    with pytest.raises(MemoryKeyError):
        entry = MemoryEntry[Dict[str, Any]](
            key="",
            value={"data": "test data"},
            type=MemoryType.SHORT_TERM,
            created_at=datetime.now(UTC),
        )
        await store._store(entry)

    # Test storing with invalid value type
    with pytest.raises(MemoryError):
        entry = MemoryEntry[Dict[str, Any]](
            key="test2",
            value="invalid",  # type: ignore
            type=MemoryType.SHORT_TERM,
            created_at=datetime.now(UTC),
        )
        await store._store(entry)


@pytest.mark.asyncio
async def test_memory_store_search() -> None:
    """Test memory store search."""
    store = create_memory_store(MemoryStoreType.MEMORY)

    # Store some test entries
    entry1 = MemoryEntry[Dict[str, Any]](
        key="user1",
        value={
            "name": "John Doe",
            "email": "john@example.com",
            "tags": ["user", "admin"],
        },
        type=MemoryType.LONG_TERM,
        metadata={"source": "test"},
        created_at=datetime.now(UTC),
    )
    await store._store(entry1)

    entry2 = MemoryEntry[Dict[str, Any]](
        key="user2",
        value={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "tags": ["user"],
        },
        type=MemoryType.LONG_TERM,
        metadata={"source": "test"},
        created_at=datetime.now(UTC),
    )
    await store._store(entry2)

    # Test basic search
    query = MemoryQuery(
        query="john",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == "user1"

    # Test search with filters
    query = MemoryQuery(
        query="user",
        index_type=MemoryIndex.SEMANTIC,
        filters={"tags": ["user"]},
        metadata={},
    )
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 2

    # Test search with metadata
    query = MemoryQuery(
        query="user",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={"source": "test"},
    )
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 2

    # Test empty query
    with pytest.raises(MemoryError):
        query = MemoryQuery(
            query="",
            index_type=MemoryIndex.SEMANTIC,
            filters={},
            metadata={},
        )
        async for _ in store._retrieve(query):
            pass


@pytest.mark.asyncio
async def test_memory_store_expiration() -> None:
    """Test memory store entry expiration."""
    store = create_memory_store(MemoryStoreType.MEMORY)

    # Store an entry that expires in 1 second
    entry = MemoryEntry[Dict[str, Any]](
        key="test1",
        value={"data": "test data"},
        type=MemoryType.SHORT_TERM,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(seconds=1),
    )
    await store._store(entry)
    assert entry.expires_at is not None

    # Verify entry can be retrieved
    query = MemoryQuery(
        query="test1",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry == entry

    # Wait for entry to expire
    await asyncio.sleep(1.1)

    # Verify entry cannot be retrieved
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 0

    # Verify expired entry is not included in search results
    query = MemoryQuery(
        query="test",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store._retrieve(query):
        results.append(result)
    assert len(results) == 0
