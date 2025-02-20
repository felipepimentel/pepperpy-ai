"""Memory module tests."""

import pytest
from datetime import UTC, datetime, timedelta

from pepperpy.memory import (
    MemoryError,
    MemoryKeyError,
    MemoryQuery,
    MemoryStoreType,
    MemoryType,
    MemoryTypeError,
    create_memory_store,
)


@pytest.mark.asyncio
async def test_memory_store_creation() -> None:
    """Test memory store creation."""
    # Test creating an in-memory store
    store = create_memory_store(MemoryStoreType.MEMORY)
    assert store is not None

    # Test creating a composite store
    store1 = create_memory_store(MemoryStoreType.MEMORY)
    store2 = create_memory_store(MemoryStoreType.MEMORY)
    composite = create_memory_store(
        MemoryStoreType.COMPOSITE,
        stores=[store1, store2],
    )
    assert composite is not None

    # Test invalid store type
    with pytest.raises(MemoryTypeError):
        create_memory_store("invalid" as MemoryStoreType)  # type: ignore


@pytest.mark.asyncio
async def test_memory_store_operations() -> None:
    """Test memory store operations."""
    store = create_memory_store(MemoryStoreType.MEMORY)

    # Test storing an entry
    entry = await store.store(
        key="test1",
        value={"data": "test data"},
        type=MemoryType.SHORT_TERM,
        metadata={"test": True},
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    assert entry.key == "test1"
    assert entry.value == {"data": "test data"}
    assert entry.type == MemoryType.SHORT_TERM
    assert entry.metadata == {"test": True}
    assert entry.expires_at is not None

    # Test retrieving an entry
    retrieved = await store.retrieve("test1")
    assert retrieved == entry

    # Test retrieving a non-existent entry
    with pytest.raises(MemoryKeyError):
        await store.retrieve("non_existent")

    # Test retrieving with type mismatch
    with pytest.raises(MemoryTypeError):
        await store.retrieve("test1", type=MemoryType.LONG_TERM)

    # Test storing with invalid key
    with pytest.raises(MemoryKeyError):
        await store.store(
            key="",
            value={"data": "test data"},
        )

    # Test storing with invalid value type
    with pytest.raises(MemoryTypeError):
        await store.store(
            key="test2",
            value="invalid",  # type: ignore
        )


@pytest.mark.asyncio
async def test_memory_store_search() -> None:
    """Test memory store search."""
    store = create_memory_store(MemoryStoreType.MEMORY)

    # Store some test entries
    await store.store(
        key="user1",
        value={
            "name": "John Doe",
            "email": "john@example.com",
            "tags": ["user", "admin"],
        },
        type=MemoryType.LONG_TERM,
        metadata={"source": "test"},
    )

    await store.store(
        key="user2",
        value={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "tags": ["user"],
        },
        type=MemoryType.LONG_TERM,
        metadata={"source": "test"},
    )

    # Test basic search
    query = MemoryQuery(query="john")
    results = []
    async for result in store.search(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == "user1"

    # Test search with filters
    query = MemoryQuery(
        query="user",
        filters={"tags": ["user"]},
    )
    results = []
    async for result in store.search(query):
        results.append(result)
    assert len(results) == 2

    # Test search with metadata
    query = MemoryQuery(
        query="user",
        metadata={"source": "test"},
    )
    results = []
    async for result in store.search(query):
        results.append(result)
    assert len(results) == 2

    # Test empty query
    with pytest.raises(MemoryError):
        query = MemoryQuery(query="")
        async for _ in store.search(query):
            pass


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
    await store1.store(
        key="test1",
        value={"data": "test1"},
        metadata={"store": "store1"},
    )

    await store2.store(
        key="test2",
        value={"data": "test2"},
        metadata={"store": "store2"},
    )

    # Store entry in composite store
    await composite.store(
        key="test3",
        value={"data": "test3"},
        metadata={"store": "composite"},
    )

    # Test retrieving entries
    entry1 = await composite.retrieve("test1")
    assert entry1.metadata["store"] == "store1"

    entry2 = await composite.retrieve("test2")
    assert entry2.metadata["store"] == "store2"

    # Test searching across stores
    query = MemoryQuery(query="test")
    results = []
    async for result in composite.search(query):
        results.append(result)
    assert len(results) == 3
