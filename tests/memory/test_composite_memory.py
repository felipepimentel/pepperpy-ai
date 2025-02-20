"""Tests for composite memory store."""

from datetime import UTC, datetime
from typing import Any, Dict

import pytest

from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemoryScope,
    MemoryType,
)
from pepperpy.memory.stores.composite import CompositeMemoryStore
from pepperpy.memory.stores.memory import InMemoryStore


@pytest.fixture
def store1() -> BaseMemoryStore[Dict[str, Any]]:
    """Create first test store."""
    return InMemoryStore()


@pytest.fixture
def store2() -> BaseMemoryStore[Dict[str, Any]]:
    """Create second test store."""
    return InMemoryStore()


@pytest.fixture
def composite_store(
    store1: BaseMemoryStore[Dict[str, Any]], store2: BaseMemoryStore[Dict[str, Any]]
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
    await composite_store.initialize()

    # Test storing an entry
    entry = MemoryEntry[Dict[str, Any]](
        key="test1",
        value={"data": "test data"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"test": "true"},
        created_at=datetime.now(UTC),
    )
    await composite_store.store(entry)

    # Test retrieving the entry
    query = MemoryQuery(
        query="test1",
        key="test1",
        filters={},
        metadata={},
    )
    results = []
    async for result in composite_store.retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == entry.key
    assert results[0].entry.value == entry.value

    # Test retrieving a non-existent entry
    query = MemoryQuery(
        query="non_existent",
        key="non_existent",
        filters={},
        metadata={},
    )
    results = []
    async for result in composite_store.retrieve(query):
        results.append(result)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_composite_store_search(composite_store: CompositeMemoryStore) -> None:
    """Test composite store search."""
    await composite_store.initialize()

    # Store entries in different stores
    entry1 = MemoryEntry[Dict[str, Any]](
        key="user1",
        value={
            "name": "John Doe",
            "email": "john@example.com",
            "tags": ["user", "admin"],
        },
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"source": "store1"},
        created_at=datetime.now(UTC),
    )
    await composite_store.store(entry1)

    entry2 = MemoryEntry[Dict[str, Any]](
        key="user2",
        value={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "tags": ["user"],
        },
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        metadata={"source": "store2"},
        created_at=datetime.now(UTC),
    )
    await composite_store.store(entry2)

    # Test basic search
    query = MemoryQuery(
        query="john",
        key=None,
        filters={},
        metadata={},
    )
    results = []
    async for result in composite_store.retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == "user1"

    # Test search with multiple results
    query = MemoryQuery(
        query="user",
        key=None,
        filters={},
        metadata={},
    )
    results = []
    async for result in composite_store.retrieve(query):
        results.append(result)
    assert len(results) == 2

    # Test search with metadata filter
    query = MemoryQuery(
        query="",
        key=None,
        filters={},
        metadata={"source": "store1"},
    )
    results = []
    async for result in composite_store.retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == "user1"


@pytest.mark.asyncio
async def test_composite_store_error_handling(
    composite_store: CompositeMemoryStore,
) -> None:
    """Test composite store error handling."""
    await composite_store.initialize()

    # Test storing with empty key
    entry = MemoryEntry[Dict[str, Any]](
        key="",
        value={"data": "test data"},
        type=MemoryType.SHORT_TERM,
        scope=MemoryScope.SESSION,
        created_at=datetime.now(UTC),
    )
    await composite_store.store(entry)

    # Test retrieving non-existent entry
    query = MemoryQuery(
        query="non_existent",
        key="non_existent",
        filters={},
        metadata={},
    )
    results = []
    async for result in composite_store.retrieve(query):
        results.append(result)
    assert len(results) == 0

    # Test empty query
    query = MemoryQuery(
        query="",
        key=None,
        filters={},
        metadata={},
    )
    results = []
    async for result in composite_store.retrieve(query):
        results.append(result)
    assert len(results) == 0
