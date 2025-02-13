"""Tests for vector memory store."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from pepperpy.memory.config import VectorStoreConfig
from pepperpy.memory.stores.vector import VectorMemoryStore
from pepperpy.memory.types import MemoryEntry, MemoryQuery, MemoryScope, MemoryType


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
def mock_model():
    """Create a mock embedding model."""
    model = Mock()
    model.encode.return_value = [[0.1, 0.2, 0.3]]
    return model


@pytest.fixture
def store(mock_model):
    """Create a test vector store."""
    with patch(
        "pepperpy.memory.stores.vector.SentenceTransformer", return_value=mock_model
    ):
        return VectorMemoryStore(
            config=VectorStoreConfig(
                model_name="all-MiniLM-L6-v2",
                storage_path=Path("tests/data/vector_store"),
            )
        )


@pytest.mark.asyncio
async def test_store_initialization(store):
    """Test store initialization."""
    await store.initialize()
    assert store._entries == {}
    assert store._vectors == {}
    assert store._model is not None
    assert store.storage_path.name == "vector_store"


@pytest.mark.asyncio
async def test_store_cleanup(store, test_entry):
    """Test store cleanup."""
    # Add test entry
    entry = MemoryEntry(**test_entry)
    async with store._lock:
        store._entries["test1"] = entry
        store._vectors["test1"] = [[0.1, 0.2, 0.3]]

    await store.cleanup()
    assert store._entries == {}
    assert store._vectors == {}


@pytest.mark.asyncio
async def test_store_get(store, test_entry):
    """Test getting entries."""
    # Add test entry
    entry = MemoryEntry(**test_entry)
    async with store._lock:
        store._entries["test1"] = entry
        store._vectors["test1"] = [[0.1, 0.2, 0.3]]

    # Test getting existing entry
    result = await store.get("test1")
    assert result is not None
    assert result.key == "test1"
    assert result.value["content"] == "test content"

    # Test getting non-existent entry
    result = await store.get("non_existent")
    assert result is None


@pytest.mark.asyncio
async def test_store_set(store, mock_model):
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
    assert "test1" in store._vectors

    # Test updating existing entry
    updated = await store.set(
        "test1",
        {"content": "updated content"},
        scope=MemoryScope.SESSION.value,
    )
    assert updated.value["content"] == "updated content"
    assert "test1" in store._vectors


@pytest.mark.asyncio
async def test_store_delete(store, test_entry):
    """Test deleting entries."""
    # Add test entry
    entry = MemoryEntry(**test_entry)
    async with store._lock:
        store._entries["test1"] = entry
        store._vectors["test1"] = [[0.1, 0.2, 0.3]]

    # Test deleting existing entry
    result = await store.delete("test1")
    assert result is True
    assert "test1" not in store._entries
    assert "test1" not in store._vectors

    # Test deleting non-existent entry
    result = await store.delete("non_existent")
    assert result is False


@pytest.mark.asyncio
async def test_store_exists(store, test_entry):
    """Test checking entry existence."""
    # Add test entry
    entry = MemoryEntry(**test_entry)
    async with store._lock:
        store._entries["test1"] = entry
        store._vectors["test1"] = [[0.1, 0.2, 0.3]]

    # Test existing entry
    assert await store.exists("test1") is True

    # Test non-existent entry
    assert await store.exists("non_existent") is False


@pytest.mark.asyncio
async def test_store_clear(store, test_entry):
    """Test clearing entries."""
    # Add test entries with different scopes
    entries = {
        "test1": MemoryEntry(
            key="test1",
            value={"content": "test content"},
            type=MemoryType.SHORT_TERM.value,
            scope=MemoryScope.SESSION.value,
            metadata={"tags": ["test"]},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=None,
            indices=set(),
        ),
        "test2": MemoryEntry(
            key="test2",
            value={"content": "test content"},
            type=MemoryType.SHORT_TERM.value,
            scope=MemoryScope.AGENT.value,
            metadata={"tags": ["test"]},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=None,
            indices=set(),
        ),
    }
    async with store._lock:
        store._entries.update(entries)
        store._vectors.update({
            "test1": [[0.1, 0.2, 0.3]],
            "test2": [[0.4, 0.5, 0.6]],
        })

    # Test clearing all entries
    count = await store.clear()
    assert count == 2
    assert store._entries == {}
    assert store._vectors == {}

    # Test clearing with scope filter
    async with store._lock:
        store._entries.update(entries)
        store._vectors.update({
            "test1": [[0.1, 0.2, 0.3]],
            "test2": [[0.4, 0.5, 0.6]],
        })
    count = await store.clear(scope=MemoryScope.SESSION.value)
    assert count == 1
    assert "test2" in store._entries
    assert "test2" in store._vectors


@pytest.mark.asyncio
async def test_store_expiration(store):
    """Test entry expiration handling."""
    # Add expired entry
    expired_entry = MemoryEntry(**{
        **test_entry(),
        "expires_at": datetime.utcnow() - timedelta(hours=1),
    })
    async with store._lock:
        store._entries["expired"] = expired_entry
        store._vectors["expired"] = [[0.1, 0.2, 0.3]]

    # Add non-expired entry
    valid_entry = MemoryEntry(**{
        **test_entry(),
        "key": "valid",
        "expires_at": datetime.utcnow() + timedelta(hours=1),
    })
    async with store._lock:
        store._entries["valid"] = valid_entry
        store._vectors["valid"] = [[0.4, 0.5, 0.6]]

    # Check expiration
    assert store._is_expired(expired_entry, datetime.utcnow()) is True
    assert store._is_expired(valid_entry, datetime.utcnow()) is False


@pytest.mark.asyncio
async def test_store_search(store, mock_model):
    """Test vector search functionality."""
    # Add test entries
    entries = [
        ("test1", "This is a test document", [[0.1, 0.2, 0.3]]),
        ("test2", "Another test document", [[0.4, 0.5, 0.6]]),
        ("test3", "Completely different content", [[0.7, 0.8, 0.9]]),
    ]

    for key, content, vector in entries:
        await store.set(key, {"content": content})
        store._vectors[key] = vector

    # Test basic search
    mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
    results = []
    async for result in store.search(MemoryQuery(query="test")):
        results.append(result)

    assert len(results) > 0
    assert results[0].entry.key == "test1"  # Most similar to query vector

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
async def test_store_concurrent_access(store, mock_model):
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
    assert len(store._vectors) == 10

    # Test concurrent searches
    mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
    results = await asyncio.gather(*[search_entries("test") for _ in range(5)])
    assert len(results) == 5
    assert all(isinstance(r, list) for r in results)


@pytest.mark.asyncio
async def test_store_vector_computation(store, mock_model):
    """Test vector computation and caching."""
    # Test vector computation
    entry = await store.set("test1", {"content": "test content"})
    vector = store._vectors["test1"]
    assert vector == [[0.1, 0.2, 0.3]]

    # Test vector caching
    mock_model.encode.reset_mock()
    entry = await store.set("test1", {"content": "test content"})
    assert mock_model.encode.call_count == 1  # Only called for new content

    # Test vector recomputation on content change
    entry = await store.set("test1", {"content": "new content"})
    assert mock_model.encode.call_count == 2  # Called again for new content


@pytest.mark.asyncio
async def test_store_error_handling(store):
    """Test error handling in vector store."""
    # Test invalid model name
    with pytest.raises(ValueError):
        VectorMemoryStore(
            config=VectorStoreConfig(
                model_name="",  # Invalid model name
                storage_path=Path("tests/data/vector_store"),
            )
        )
