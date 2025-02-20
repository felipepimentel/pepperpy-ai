"""Composite memory store tests."""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from pepperpy.memory.base import (
    MemoryEntry,
    MemoryIndex,
    MemoryQuery,
    MemoryScope,
    MemoryType,
)
from pepperpy.memory.stores.composite import CompositeMemoryStore
from pepperpy.memory.stores.memory import InMemoryStore


@pytest.fixture
def store1() -> InMemoryStore:
    """Create first test store."""
    return InMemoryStore(name="store1", config={})


@pytest.fixture
def store2() -> InMemoryStore:
    """Create second test store."""
    return InMemoryStore(name="store2", config={})


@pytest.fixture
def composite_store(
    store1: InMemoryStore, store2: InMemoryStore
) -> CompositeMemoryStore:
    """Create composite store with test stores."""
    return CompositeMemoryStore(name="composite", stores=[store1, store2])


@pytest.mark.asyncio
async def test_composite_store_initialization(
    composite_store: CompositeMemoryStore,
) -> None:
    """Test composite store initialization."""
    await composite_store.initialize()
    assert len(composite_store._stores) == 2


@pytest.mark.asyncio
async def test_composite_store_operations(
    composite_store: CompositeMemoryStore,
) -> None:
    """Test composite store operations."""
    # Test storing an entry
    entry = MemoryEntry[Dict[str, Any]](
        key="test1",
        value={"data": "test data"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"test": True},
        created_at=datetime.now(timezone.utc),
    )
    await composite_store._store(entry)

    # Test retrieving the entry
    query = MemoryQuery(
        query=entry.key, index_type=MemoryIndex.SEMANTIC, filters={}, metadata={}
    )
    results = []
    async for result in composite_store._retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == entry.key
    assert results[0].entry.value == entry.value

    # Test retrieving a non-existent entry
    query = MemoryQuery(
        query="non_existent", index_type=MemoryIndex.SEMANTIC, filters={}, metadata={}
    )
    results = []
    async for result in composite_store._retrieve(query):
        results.append(result)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_composite_store_search(composite_store: CompositeMemoryStore) -> None:
    """Test composite store search."""
    # Store entries in different stores
    entry1 = MemoryEntry[Dict[str, Any]](
        key="user1",
        value={
            "name": "John Doe",
            "email": "john@example.com",
            "tags": ["user", "admin"],
        },
        type=MemoryType.LONG_TERM,
        scope=MemoryScope.GLOBAL,
        metadata={"source": "store1"},
        created_at=datetime.now(timezone.utc),
    )
    await composite_store._store(entry1)

    entry2 = MemoryEntry[Dict[str, Any]](
        key="user2",
        value={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "tags": ["user"],
        },
        type=MemoryType.LONG_TERM,
        scope=MemoryScope.GLOBAL,
        metadata={"source": "store2"},
        created_at=datetime.now(timezone.utc),
    )
    await composite_store._store(entry2)

    # Test basic search
    query = MemoryQuery(
        query="john",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in composite_store._retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == entry1.key
    assert results[0].entry.metadata["source"] == "store1"

    # Test search with filters
    query = MemoryQuery(
        query="user",
        index_type=MemoryIndex.SEMANTIC,
        filters={"tags": ["user"]},
        metadata={},
    )
    results = []
    async for result in composite_store._retrieve(query):
        results.append(result)
    assert len(results) == 2

    # Test search with metadata
    query = MemoryQuery(
        query="user",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={"source": "store1"},
    )
    results = []
    async for result in composite_store._retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.metadata["source"] == "store1"


@pytest.mark.asyncio
async def test_composite_store_error_handling(
    composite_store: CompositeMemoryStore,
) -> None:
    """Test composite store error handling."""
    # Test storing with invalid key
    with pytest.raises(ValueError):
        entry = MemoryEntry[Dict[str, Any]](
            key="",
            value={"data": "test data"},
            type=MemoryType.SHORT_TERM,
            scope=MemoryScope.SESSION,
            created_at=datetime.now(timezone.utc),
        )
        await composite_store._store(entry)

    # Test storing with invalid value type
    with pytest.raises(TypeError):
        entry = MemoryEntry[Dict[str, Any]](
            key="test2",
            value="invalid",  # type: ignore
            type=MemoryType.SHORT_TERM,
            scope=MemoryScope.SESSION,
            created_at=datetime.now(timezone.utc),
        )
        await composite_store._store(entry)

    # Test searching with empty query
    with pytest.raises(ValueError):
        query = MemoryQuery(
            query="",
            index_type=MemoryIndex.SEMANTIC,
            filters={},
            metadata={},
        )
        async for _ in composite_store._retrieve(query):
            pass
