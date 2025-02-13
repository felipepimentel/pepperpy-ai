"""Tests for PostgreSQL memory store."""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest

from pepperpy.memory.stores.postgres import PostgresMemoryStore
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
def mock_pool():
    """Create a mock database pool."""
    pool = AsyncMock()
    pool.acquire = AsyncMock()
    pool.release = AsyncMock()
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def mock_connection():
    """Create a mock database connection."""
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.fetchval = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetchall = AsyncMock()
    return conn


@pytest.fixture
def store(mock_pool, mock_connection):
    """Create a test PostgreSQL store."""
    mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
    with patch("asyncpg.create_pool", return_value=mock_pool):
        return PostgresMemoryStore(
            name="test_store",
            dsn="postgresql://test_user:test_pass@localhost:5432/test_db",
            schema="memory",
            table="entries",
        )


@pytest.mark.asyncio
async def test_store_initialization(store, mock_pool, mock_connection):
    """Test store initialization."""
    # Test table creation
    await store.initialize()
    assert mock_pool.acquire.called
    assert mock_connection.execute.called
    assert "CREATE TABLE IF NOT EXISTS" in mock_connection.execute.call_args[0][0]


@pytest.mark.asyncio
async def test_store_cleanup(store, mock_pool, mock_connection):
    """Test store cleanup."""
    await store.cleanup()
    assert mock_pool.close.called


@pytest.mark.asyncio
async def test_store_get(store, mock_pool, mock_connection, test_entry):
    """Test getting entries."""
    # Mock entry retrieval
    mock_connection.fetchrow.return_value = test_entry

    # Test getting existing entry
    result = await store.get("test1")
    assert result is not None
    assert result.key == "test1"
    assert result.value["content"] == "test content"
    assert "SELECT * FROM memory_entries" in mock_connection.fetchrow.call_args[0][0]

    # Test getting non-existent entry
    mock_connection.fetchrow.return_value = None
    result = await store.get("non_existent")
    assert result is None


@pytest.mark.asyncio
async def test_store_set(store, mock_pool, mock_connection):
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
    assert "INSERT INTO memory_entries" in mock_connection.execute.call_args[0][0]

    # Test updating existing entry
    updated = await store.set(
        "test1",
        {"content": "updated content"},
        scope=MemoryScope.SESSION.value,
    )
    assert updated.value["content"] == "updated content"
    assert "UPDATE memory_entries" in mock_connection.execute.call_args[0][0]


@pytest.mark.asyncio
async def test_store_delete(store, mock_pool, mock_connection):
    """Test deleting entries."""
    # Test deleting existing entry
    mock_connection.fetchval.return_value = True
    result = await store.delete("test1")
    assert result is True
    assert "DELETE FROM memory_entries" in mock_connection.execute.call_args[0][0]

    # Test deleting non-existent entry
    mock_connection.fetchval.return_value = False
    result = await store.delete("non_existent")
    assert result is False


@pytest.mark.asyncio
async def test_store_exists(store, mock_pool, mock_connection):
    """Test checking entry existence."""
    # Test existing entry
    mock_connection.fetchval.return_value = True
    assert await store.exists("test1") is True
    assert "SELECT EXISTS" in mock_connection.fetchval.call_args[0][0]

    # Test non-existent entry
    mock_connection.fetchval.return_value = False
    assert await store.exists("non_existent") is False


@pytest.mark.asyncio
async def test_store_clear(store, mock_pool, mock_connection):
    """Test clearing entries."""
    # Test clearing all entries
    mock_connection.fetchval.return_value = 2
    count = await store.clear()
    assert count == 2
    assert "DELETE FROM memory_entries" in mock_connection.execute.call_args[0][0]

    # Test clearing with scope filter
    mock_connection.fetchval.return_value = 1
    count = await store.clear(scope=MemoryScope.SESSION.value)
    assert count == 1
    assert "WHERE scope = $1" in mock_connection.execute.call_args[0][0]


@pytest.mark.asyncio
async def test_store_expiration(store, mock_pool, mock_connection):
    """Test entry expiration handling."""
    # Test expired entry cleanup
    await store.cleanup_expired()
    assert "DELETE FROM memory_entries" in mock_connection.execute.call_args[0][0]
    assert "expires_at IS NOT NULL" in mock_connection.execute.call_args[0][0]
    assert "expires_at <= NOW()" in mock_connection.execute.call_args[0][0]


@pytest.mark.asyncio
async def test_store_search(store, mock_pool, mock_connection, test_entry):
    """Test search functionality."""
    # Mock search results
    mock_connection.fetchall.return_value = [test_entry]

    # Test basic search
    results = []
    async for result in store.search(MemoryQuery(query="test")):
        results.append(result)

    assert len(results) > 0
    assert results[0].entry.key == "test1"
    assert "SELECT * FROM memory_entries" in mock_connection.fetchall.call_args[0][0]

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
    assert "WHERE type = $1" in mock_connection.fetchall.call_args[0][0]


@pytest.mark.asyncio
async def test_store_concurrent_access(store, mock_pool, mock_connection):
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
    assert mock_connection.execute.call_count >= 10

    # Test concurrent searches
    mock_connection.fetchall.return_value = []
    results = await asyncio.gather(*[search_entries("test") for _ in range(5)])
    assert len(results) == 5
    assert all(isinstance(r, list) for r in results)


@pytest.mark.asyncio
async def test_store_error_handling(store):
    """Test error handling in PostgreSQL store."""
    # Test invalid connection parameters
    with pytest.raises(ValueError):
        PostgresMemoryStore(
            name="test_store",
            dsn="",  # Invalid DSN
            schema="memory",
            table="entries",
        )
