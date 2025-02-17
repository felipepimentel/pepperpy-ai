"""Composite memory store tests."""

from datetime import UTC, datetime, timedelta

import pytest

from pepperpy.core.memory import (
    MemoryError,
    MemoryKeyError,
    MemoryQuery,
    MemoryStoreType,
    MemoryType,
    create_memory_store,
)


@pytest.mark.asyncio
async def test_composite_store_creation() -> None:
    """Test composite store creation."""
    # Test creating a composite store with no stores
    store = create_memory_store(MemoryStoreType.COMPOSITE)
    assert store is not None

    # Test creating a composite store with stores
    store1 = create_memory_store(MemoryStoreType.MEMORY)
    store2 = create_memory_store(MemoryStoreType.MEMORY)
    composite = create_memory_store(
        MemoryStoreType.COMPOSITE,
        stores=[store1, store2],
    )
    assert composite is not None


@pytest.mark.asyncio
async def test_composite_store_operations() -> None:
    """Test composite store operations."""
    # Create stores
    store1 = create_memory_store(MemoryStoreType.MEMORY)
    store2 = create_memory_store(MemoryStoreType.MEMORY)
    composite = create_memory_store(
        MemoryStoreType.COMPOSITE,
        stores=[store1, store2],
    )

    # Test storing an entry
    entry = await composite.store(
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

    # Verify entry is stored in all stores
    entry1 = await store1.retrieve("test1")
    assert entry1 == entry

    entry2 = await store2.retrieve("test1")
    assert entry2 == entry

    # Test retrieving a non-existent entry
    with pytest.raises(MemoryKeyError):
        await composite.retrieve("non_existent")

    # Test retrieving with type mismatch
    with pytest.raises(MemoryError):
        await composite.retrieve("test1", type=MemoryType.LONG_TERM)


@pytest.mark.asyncio
async def test_composite_store_search() -> None:
    """Test composite store search."""
    # Create stores
    store1 = create_memory_store(MemoryStoreType.MEMORY)
    store2 = create_memory_store(MemoryStoreType.MEMORY)
    composite = create_memory_store(
        MemoryStoreType.COMPOSITE,
        stores=[store1, store2],
    )

    # Store entries in different stores
    await store1.store(
        key="user1",
        value={
            "name": "John Doe",
            "email": "john@example.com",
            "tags": ["user", "admin"],
        },
        type=MemoryType.LONG_TERM,
        metadata={"source": "store1"},
    )

    await store2.store(
        key="user2",
        value={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "tags": ["user"],
        },
        type=MemoryType.LONG_TERM,
        metadata={"source": "store2"},
    )

    # Test basic search
    query = MemoryQuery(query="john")
    results = []
    async for result in composite.search(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.key == "user1"
    assert results[0].entry.metadata["source"] == "store1"

    # Test search with filters
    query = MemoryQuery(
        query="user",
        filters={"tags": ["user"]},
    )
    results = []
    async for result in composite.search(query):
        results.append(result)
    assert len(results) == 2

    # Test search with metadata
    query = MemoryQuery(
        query="user",
        metadata={"source": "store1"},
    )
    results = []
    async for result in composite.search(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry.metadata["source"] == "store1"


@pytest.mark.asyncio
async def test_composite_store_error_handling() -> None:
    """Test composite store error handling."""
    # Create stores
    store1 = create_memory_store(MemoryStoreType.MEMORY)
    store2 = create_memory_store(MemoryStoreType.MEMORY)
    composite = create_memory_store(
        MemoryStoreType.COMPOSITE,
        stores=[store1, store2],
    )

    # Test storing with invalid key
    with pytest.raises(MemoryKeyError):
        await composite.store(
            key="",
            value={"data": "test data"},
        )

    # Test storing with invalid value type
    with pytest.raises(MemoryError):
        await composite.store(
            key="test2",
            value="invalid",  # type: ignore
        )

    # Test retrieving from empty stores
    with pytest.raises(MemoryKeyError):
        await composite.retrieve("non_existent")

    # Test searching with empty query
    with pytest.raises(MemoryError):
        query = MemoryQuery(query="")
        async for _ in composite.search(query):
            pass
