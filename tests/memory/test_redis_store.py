"""Tests for Redis memory store."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest

from pepperpy.memory.config import RedisConfig
from pepperpy.memory.stores.redis import RedisMemoryStore
from pepperpy.memory.types import MemoryQuery, MemoryScope, MemoryType


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
def mock_redis():
    """Create a mock Redis client."""
    client = AsyncMock()
    client.set = AsyncMock()
    client.get = AsyncMock()
    client.delete = AsyncMock()
    client.exists = AsyncMock()
    client.scan = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def store(mock_redis):
    """Create a test Redis store."""
    with (
        patch("redis.asyncio.ConnectionPool"),
        patch("redis.asyncio.Redis", return_value=mock_redis),
    ):
        store = RedisMemoryStore(
            config=RedisConfig(
                host="localhost",
                port=6379,
                db=0,
                prefix="test",
            )
        )
        store._client = mock_redis
        return store


@pytest.mark.asyncio
async def test_store_initialization(store, mock_redis):
    """Test store initialization."""
    await store.initialize()
    assert store._client is not None
    assert store._pool is not None


@pytest.mark.asyncio
async def test_store_cleanup(store, mock_redis):
    """Test store cleanup."""
    await store.cleanup()
    assert mock_redis.close.called


@pytest.mark.asyncio
async def test_store_get(store, mock_redis, test_entry):
    """Test getting entries."""
    # Mock entry retrieval
    mock_redis.get.return_value = json.dumps(test_entry)

    # Test getting existing entry
    result = await store.get("test1")
    assert result is not None
    assert result.key == "test1"
    assert result.value["content"] == "test content"
    assert mock_redis.get.called

    # Test getting non-existent entry
    mock_redis.get.return_value = None
    result = await store.get("non_existent")
    assert result is None


@pytest.mark.asyncio
async def test_store_set(store, mock_redis):
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
    assert mock_redis.set.called

    # Test updating existing entry
    updated = await store.set(
        "test1",
        {"content": "updated content"},
        scope=MemoryScope.SESSION.value,
    )
    assert updated.value["content"] == "updated content"
    assert mock_redis.set.call_count == 2


@pytest.mark.asyncio
async def test_store_delete(store, mock_redis):
    """Test deleting entries."""
    # Test deleting existing entry
    mock_redis.delete.return_value = 1
    result = await store.delete("test1")
    assert result is True
    assert mock_redis.delete.called

    # Test deleting non-existent entry
    mock_redis.delete.return_value = 0
    result = await store.delete("non_existent")
    assert result is False


@pytest.mark.asyncio
async def test_store_exists(store, mock_redis):
    """Test checking entry existence."""
    # Test existing entry
    mock_redis.exists.return_value = 1
    assert await store.exists("test1") is True
    assert mock_redis.exists.called

    # Test non-existent entry
    mock_redis.exists.return_value = 0
    assert await store.exists("non_existent") is False


@pytest.mark.asyncio
async def test_store_clear(store, mock_redis):
    """Test clearing entries."""
    # Mock scan results
    mock_redis.scan.side_effect = [
        (0, [b"test:key1", b"test:key2"]),  # First scan
        (0, []),  # No more keys
    ]
    mock_redis.delete.return_value = 2

    # Test clearing all entries
    count = await store.clear()
    assert count == 2
    assert mock_redis.scan.called
    assert mock_redis.delete.called

    # Test clearing with scope filter
    mock_redis.scan.side_effect = [
        (0, [b"test:key1"]),  # First scan
        (0, []),  # No more keys
    ]
    mock_redis.get.return_value = json.dumps({
        **test_entry(),
        "scope": MemoryScope.SESSION.value,
    })
    mock_redis.delete.return_value = 1

    count = await store.clear(scope=MemoryScope.SESSION.value)
    assert count == 1


@pytest.mark.asyncio
async def test_store_expiration(store, mock_redis):
    """Test entry expiration handling."""
    # Mock scan results for expired entries
    mock_redis.scan.side_effect = [
        (0, [b"test:expired1", b"test:expired2"]),  # First scan
        (0, []),  # No more keys
    ]
    mock_redis.get.side_effect = [
        json.dumps({
            **test_entry(),
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        }),
        json.dumps({
            **test_entry(),
            "key": "expired2",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        }),
    ]
    mock_redis.delete.return_value = 2

    # Test expired entry cleanup
    await store.cleanup_expired()
    assert mock_redis.scan.called
    assert mock_redis.delete.called


@pytest.mark.asyncio
async def test_store_search(store, mock_redis, test_entry):
    """Test search functionality."""
    # Mock scan results
    mock_redis.scan.side_effect = [
        (0, [b"test:key1", b"test:key2"]),  # First scan
        (0, []),  # No more keys
    ]
    mock_redis.get.side_effect = [
        json.dumps(test_entry),
        json.dumps({**test_entry, "key": "key2"}),
    ]

    # Test basic search
    results = []
    async for result in store.search(MemoryQuery(query="test")):
        results.append(result)

    assert len(results) > 0
    assert results[0].entry.key == "test1"
    assert mock_redis.scan.called
    assert mock_redis.get.called

    # Test search with filters
    mock_redis.scan.side_effect = [
        (0, [b"test:key1"]),  # First scan
        (0, []),  # No more keys
    ]
    mock_redis.get.return_value = json.dumps({
        **test_entry,
        "type": MemoryType.SHORT_TERM.value,
    })

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
async def test_store_concurrent_access(store, mock_redis):
    """Test concurrent access to the store."""

    async def write_entry(key: str, content: str) -> None:
        await store.set(key, {"content": content})

    async def search_entries(query: str) -> list:
        results = []
        async for result in store.search(MemoryQuery(query=query)):
            results.append(result)
        return results

    # Mock scan results for concurrent searches
    mock_redis.scan.side_effect = [
        (0, [b"test:key1"]),  # First scan
        (0, []),  # No more keys
    ] * 5  # For 5 concurrent searches
    mock_redis.get.return_value = json.dumps(test_entry())

    # Test concurrent writes
    await asyncio.gather(*[write_entry(f"key{i}", f"content{i}") for i in range(10)])
    assert mock_redis.set.call_count == 10

    # Test concurrent searches
    results = await asyncio.gather(*[search_entries("test") for _ in range(5)])
    assert len(results) == 5
    assert all(isinstance(r, list) for r in results)


@pytest.mark.asyncio
async def test_store_error_handling(store):
    """Test error handling in Redis store."""
    # Test invalid connection parameters
    with pytest.raises(ValueError):
        RedisMemoryStore(
            config=RedisConfig(
                host="",  # Invalid host
                port=6379,
                db=0,
                prefix="test",
            )
        )
