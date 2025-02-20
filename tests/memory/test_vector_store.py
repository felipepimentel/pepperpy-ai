"""Vector store tests."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from pepperpy.memory import (
    MemoryQuery,
    MemorySearchResult,
    MemoryType,
)
from pepperpy.memory.config import StoreType, VectorStoreConfig
from pepperpy.memory.stores.types import VectorMemoryEntry
from pepperpy.memory.stores.vector import VectorStore


@pytest.fixture
def test_entry() -> Dict[str, Any]:
    """Create a test memory entry."""
    return {
        "data": "test data",
        "metadata": {"test": True},
        "tags": ["test", "memory"],
    }


@pytest.fixture
def mock_model() -> Mock:
    """Create a mock model."""
    mock = Mock()
    mock.encode.return_value = [0.1, 0.2, 0.3]  # Mock embedding
    return mock


@pytest.fixture
def store(mock_model: Mock) -> VectorStore:
    """Create a vector store instance."""
    config = VectorStoreConfig(
        store_type=StoreType.VECTOR,
        model_name="test-model",
        dimension=3,  # Match mock embedding dimension
    )
    with patch(
        "pepperpy.memory.stores.vector.SentenceTransformer", return_value=mock_model
    ):
        store = VectorStore(config=config)
    return store


@pytest.mark.asyncio
async def test_store_initialization(store: VectorStore) -> None:
    """Test store initialization."""
    assert store is not None
    assert store._vectors == {}
    assert store._entries == {}


@pytest.mark.asyncio
async def test_store_cleanup(store: VectorStore, test_entry: Dict[str, Any]) -> None:
    """Test store cleanup."""
    # Store test entry
    entry = VectorMemoryEntry(
        key="test1",
        value=test_entry,
        type=MemoryType.SHORT_TERM,
        metadata={},
        created_at=datetime.now(timezone.utc),
        embedding=[0.1, 0.2, 0.3],
    )
    await store.store(entry)

    # Verify entry is stored
    assert len(store._entries) == 1
    assert len(store._vectors) == 1

    # Clean up store
    await store.cleanup()

    # Verify store is empty
    assert len(store._entries) == 0
    assert len(store._vectors) == 0


@pytest.mark.asyncio
async def test_store_retrieve(store: VectorStore, test_entry: Dict[str, Any]) -> None:
    """Test store retrieval."""
    # Store test entry
    entry = VectorMemoryEntry(
        key="test1",
        value=test_entry,
        type=MemoryType.SHORT_TERM,
        metadata={},
        created_at=datetime.now(timezone.utc),
        embedding=[0.1, 0.2, 0.3],
    )
    await store.store(entry)

    # Retrieve entry
    query = MemoryQuery(key="test1", query="test data")
    results = []
    async for result in store.retrieve(query):
        results.append(result)

    # Verify retrieval
    assert len(results) == 1
    assert results[0].entry.key == "test1"
    assert results[0].entry.value == test_entry


@pytest.mark.asyncio
async def test_store_store(store: VectorStore, mock_model: Mock) -> None:
    """Test storing entries."""
    # Create test entries
    entries = [
        VectorMemoryEntry(
            key=f"test{i}",
            value={"data": f"test data {i}"},
            type=MemoryType.SHORT_TERM,
            metadata={},
            created_at=datetime.now(timezone.utc),
            embedding=[0.1, 0.2, 0.3],
        )
        for i in range(3)
    ]

    # Store entries
    for entry in entries:
        await store.store(entry)

    # Verify storage
    assert len(store._entries) == 3
    assert len(store._vectors) == 3

    # Verify entries are stored correctly
    for i, entry in enumerate(entries):
        assert store._entries[str(entry.id)].value == {"data": f"test data {i}"}
        assert store._vectors[str(entry.id)] is not None


@pytest.mark.asyncio
async def test_store_delete(store: VectorStore, test_entry: Dict[str, Any]) -> None:
    """Test deleting entries."""
    # Store test entry
    entry = VectorMemoryEntry(
        key="test1",
        value=test_entry,
        type=MemoryType.SHORT_TERM,
        metadata={},
        created_at=datetime.now(timezone.utc),
        embedding=[0.1, 0.2, 0.3],
    )
    await store.store(entry)

    # Delete entry
    await store.delete(str(entry.id))

    # Verify deletion
    assert str(entry.id) not in store._entries
    assert str(entry.id) not in store._vectors


@pytest.mark.asyncio
async def test_store_clear(store: VectorStore, test_entry: Dict[str, Any]) -> None:
    """Test clearing store."""
    # Store multiple entries
    entries = [
        VectorMemoryEntry(
            key=f"test{i}",
            value={"data": f"test data {i}"},
            type=MemoryType.SHORT_TERM,
            metadata={},
            created_at=datetime.now(timezone.utc),
            embedding=[0.1, 0.2, 0.3],
        )
        for i in range(3)
    ]

    for entry in entries:
        await store.store(entry)

    # Verify entries are stored
    assert len(store._entries) == 3
    assert len(store._vectors) == 3

    # Clear store
    await store.clear()

    # Verify store is empty
    assert len(store._entries) == 0
    assert len(store._vectors) == 0


@pytest.mark.asyncio
async def test_store_expiration(store: VectorStore) -> None:
    """Test entry expiration."""
    # Store entry that expires in 1 second
    entry = VectorMemoryEntry(
        key="test1",
        value={"data": "test data"},
        type=MemoryType.SHORT_TERM,
        metadata={},
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=1),
        embedding=[0.1, 0.2, 0.3],
    )
    await store.store(entry)

    # Verify entry exists
    query = MemoryQuery(key=str(entry.id), query="test data")
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 1

    # Wait for entry to expire
    await asyncio.sleep(1.1)

    # Verify entry is expired
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_store_search(store: VectorStore, mock_model: Mock) -> None:
    """Test searching entries."""
    # Store test entries
    entries = [
        VectorMemoryEntry(
            key=f"test{i}",
            value={
                "name": f"Test {i}",
                "data": f"test data {i}",
                "tags": ["test", f"tag{i}"],
            },
            type=MemoryType.SHORT_TERM,
            metadata={"source": "test"},
            created_at=datetime.now(timezone.utc),
            embedding=[0.1, 0.2, 0.3],
        )
        for i in range(3)
    ]

    for entry in entries:
        await store.store(entry)

    # Search entries
    query = MemoryQuery(query="test data")
    results = []
    async for result in store.search(query):
        results.append(result)

    # Verify search results
    assert len(results) == 3
    assert all(isinstance(r, MemorySearchResult) for r in results)
    assert all(r.score > 0 for r in results)


@pytest.mark.asyncio
async def test_store_concurrent_access(store: VectorStore, mock_model: Mock) -> None:
    """Test concurrent store access."""

    async def write_entry(key: str, content: str) -> None:
        entry = VectorMemoryEntry(
            key=key,
            value={"data": content},
            type=MemoryType.SHORT_TERM,
            metadata={},
            created_at=datetime.now(timezone.utc),
            embedding=[0.1, 0.2, 0.3],
        )
        await store.store(entry)

    async def search_entries(query: str) -> List[Any]:
        results = []
        async for result in store.search(MemoryQuery(query=query)):
            results.append(result)
        return results

    # Run concurrent operations
    await asyncio.gather(
        write_entry("k1", "test1"),
        write_entry("k2", "test2"),
        search_entries("test"),
    )

    # Verify final state
    assert len(store._entries) == 2
    assert len(store._vectors) == 2
