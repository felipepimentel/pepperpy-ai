"""Tests for memory compatibility layer."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import Mock

import pytest

from pepperpy.memory.compat import BaseMemory, CompatMemoryStore
from pepperpy.memory.stores.inmemory import InMemoryStore
from pepperpy.memory.types import (
    MemoryEntry,
    MemoryResult,
    MemoryScope,
    MemoryType,
)


@pytest.fixture
def test_entry() -> Dict[str, Any]:
    """Create a test memory entry."""
    return {
        "key": "test1",
        "value": {"content": "test content"},
        "type": MemoryType.SHORT_TERM,
        "scope": MemoryScope.SESSION,
        "metadata": {"tags": ["test"]},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "expires_at": None,
        "indices": set(),
    }


@pytest.fixture
def store():
    """Create a test memory store."""
    return InMemoryStore({})


@pytest.fixture
def compat_store(store):
    """Create a compatibility wrapper."""
    return CompatMemoryStore(store)


@pytest.mark.asyncio
async def test_base_memory_interface():
    """Test base memory interface."""

    class TestMemory(BaseMemory[str, Dict[str, Any]]):
        async def store(self, *args, **kwargs):
            pass

        async def retrieve(self, *args, **kwargs):
            pass

        async def search(self, *args, **kwargs):
            pass

        async def similar(self, *args, **kwargs):
            pass

    memory = TestMemory()
    assert isinstance(memory, BaseMemory)


@pytest.mark.asyncio
async def test_compat_store_initialization(store, compat_store):
    """Test compatibility store initialization."""
    assert compat_store._store == store
    assert isinstance(compat_store._lock, asyncio.Lock)


@pytest.mark.asyncio
async def test_compat_store_store(compat_store, test_entry):
    """Test storing entries through compatibility layer."""
    # Test storing new entry
    entry = await compat_store.store(
        key="test1",
        value={"content": "test content"},
        type=str(MemoryType.SHORT_TERM),
        scope=str(MemoryScope.SESSION),
        metadata={"tags": ["test"]},
    )
    assert entry.key == "test1"
    assert entry.value["content"] == "test content"
    assert entry.type == str(MemoryType.SHORT_TERM)
    assert entry.scope == str(MemoryScope.SESSION)
    assert entry.metadata == {"tags": ["test"]}

    # Test storing with expiration
    expires_at = datetime.utcnow() + timedelta(hours=1)
    entry = await compat_store.store(
        key="test2",
        value={"content": "test content"},
        expires_at=expires_at,
    )
    assert entry.expires_at == expires_at


@pytest.mark.asyncio
async def test_compat_store_retrieve(compat_store, test_entry):
    """Test retrieving entries through compatibility layer."""
    # Store test entry
    await compat_store.store(
        key="test1",
        value=test_entry["value"],
        type=str(test_entry["type"]),
        scope=str(test_entry["scope"]),
        metadata=test_entry["metadata"],
    )

    # Test retrieving by key
    entry = await compat_store.retrieve("test1")
    assert entry.key == "test1"
    assert entry.value == test_entry["value"]

    # Test retrieving with type filter
    entry = await compat_store.retrieve("test1", type=str(MemoryType.SHORT_TERM))
    assert entry is not None

    # Test retrieving non-existent entry
    with pytest.raises(RuntimeError):
        await compat_store.retrieve("non_existent")


@pytest.mark.asyncio
async def test_compat_store_search(compat_store, test_entry):
    """Test searching entries through compatibility layer."""
    # Store test entries
    await compat_store.store(
        key="test1",
        value={"content": "test content"},
        type=str(MemoryType.SHORT_TERM),
        scope=str(MemoryScope.SESSION),
    )
    await compat_store.store(
        key="test2",
        value={"content": "other content"},
        type=str(MemoryType.SHORT_TERM),
        scope=str(MemoryScope.SESSION),
    )

    # Test basic search
    async for result in compat_store.search("test"):
        assert isinstance(result, MemoryResult)
        assert result.entry.value["content"] in ["test content", "other content"]

    # Test search with type filter
    async for result in compat_store.search(
        "test",
        type=str(MemoryType.SHORT_TERM),
    ):
        assert result.entry.type == str(MemoryType.SHORT_TERM)

    # Test search with scope filter
    async for result in compat_store.search(
        "test",
        scope=str(MemoryScope.SESSION),
    ):
        assert result.entry.scope == str(MemoryScope.SESSION)


@pytest.mark.asyncio
async def test_compat_store_list(compat_store, test_entry):
    """Test listing entries through compatibility layer."""
    # Store test entries
    await compat_store.store(
        key="test1",
        value={"content": "test content"},
        type=str(MemoryType.SHORT_TERM),
        scope=str(MemoryScope.SESSION),
    )
    await compat_store.store(
        key="test2",
        value={"content": "other content"},
        type=str(MemoryType.LONG_TERM),
        scope=str(MemoryScope.AGENT),
    )

    # Test listing all entries
    entries = []
    async for entry in compat_store.list():
        entries.append(entry)
    assert len(entries) == 2

    # Test listing with type filter
    entries = []
    async for entry in compat_store.list(type=str(MemoryType.SHORT_TERM)):
        entries.append(entry)
    assert len(entries) == 1
    assert entries[0].type == str(MemoryType.SHORT_TERM)

    # Test listing with scope filter
    entries = []
    async for entry in compat_store.list(scope=str(MemoryScope.SESSION)):
        entries.append(entry)
    assert len(entries) == 1
    assert entries[0].scope == str(MemoryScope.SESSION)

    # Test listing with pattern
    entries = []
    async for entry in compat_store.list(pattern="test"):
        entries.append(entry)
    assert len(entries) == 1
    assert "test" in entries[0].value["content"]


@pytest.mark.asyncio
async def test_compat_store_type_conversion():
    """Test type conversion between old and new formats."""
    # Test memory type conversion
    assert str(MemoryType.SHORT_TERM) == "short_term"
    assert str(MemoryType.LONG_TERM) == "long_term"
    assert str(MemoryType.WORKING) == "working"

    # Test memory scope conversion
    assert str(MemoryScope.SESSION) == "session"
    assert str(MemoryScope.AGENT) == "agent"
    assert str(MemoryScope.GLOBAL) == "global"


@pytest.mark.asyncio
async def test_compat_store_error_handling(compat_store):
    """Test error handling in compatibility layer."""
    # Test store error
    with pytest.raises(RuntimeError):
        await compat_store.store(key="", value={})  # Invalid key

    # Test retrieve error
    with pytest.raises(RuntimeError):
        await compat_store.retrieve("")  # Invalid key

    # Test search error
    mock_store = Mock(spec=InMemoryStore)
    mock_store.retrieve.side_effect = Exception("Test error")
    error_store = CompatMemoryStore(mock_store)

    with pytest.raises(RuntimeError):
        async for _ in error_store.search("test"):
            pass


@pytest.mark.asyncio
async def test_compat_store_concurrent_access(compat_store):
    """Test concurrent access through compatibility layer."""

    async def store_entry(key: str, value: dict) -> None:
        await compat_store.store(key=key, value=value)

    async def retrieve_entry(key: str) -> MemoryEntry:
        return await compat_store.retrieve(key)

    # Test concurrent stores
    await asyncio.gather(*[
        store_entry(f"key{i}", {"value": f"value{i}"}) for i in range(10)
    ])

    # Test concurrent retrieves
    results = await asyncio.gather(*[retrieve_entry(f"key{i}") for i in range(10)])
    assert len(results) == 10
    assert all(r.value["value"] == f"value{i}" for i, r in enumerate(results))
