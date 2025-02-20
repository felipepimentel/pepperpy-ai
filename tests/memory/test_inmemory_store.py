"""In-memory store tests."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import pytest

from pepperpy.memory.stores.inmemory import InMemoryStore
from pepperpy.memory.types import (
    MemoryIndex,
    MemoryQuery,
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
        "metadata": {"tags": "test"},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "expires_at": None,
        "indices": set(),
    }


@pytest.fixture
def store() -> InMemoryStore:
    """Create a test in-memory store."""
    return InMemoryStore(config={})


@pytest.mark.asyncio
async def test_store_initialization(store: InMemoryStore) -> None:
    """Test store initialization."""
    await store.initialize()
    assert await store.exists("test1") is False


@pytest.mark.asyncio
async def test_store_cleanup(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test store cleanup."""
    # Add test entry
    entry = await store.store(
        key=test_entry["key"],
        content=test_entry["value"],
        scope=test_entry["scope"],
        metadata=test_entry["metadata"],
    )

    await store.cleanup()
    assert await store.exists("test1") is False


@pytest.mark.asyncio
async def test_store_get(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test getting entries."""
    # Add test entry
    entry = await store.store(
        key=test_entry["key"],
        content=test_entry["value"],
        scope=test_entry["scope"],
        metadata=test_entry["metadata"],
    )

    # Test getting existing entry
    query = MemoryQuery(
        query="test1",
        key="test1",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)

    assert len(results) == 1
    assert results[0].key == "test1"
    assert results[0].entry["content"] == "test content"

    # Test getting non-existent entry
    query = MemoryQuery(
        query="non_existent",
        key="non_existent",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_store_store(store: InMemoryStore) -> None:
    """Test storing entries."""
    # Test storing new entry
    entry = await store.store(
        key="test1",
        content={"content": "test content"},
        scope=MemoryScope.SESSION,
        metadata={"tags": "test"},
    )
    assert await store.exists("test1") is True

    # Test updating existing entry
    updated = await store.store(
        key="test1",
        content={"content": "updated content"},
        scope=MemoryScope.SESSION,
        metadata={"tags": "test"},
    )
    query = MemoryQuery(
        query="test1",
        key="test1",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) == 1
    assert results[0].entry["content"] == "updated content"


@pytest.mark.asyncio
async def test_store_delete(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test deleting entries."""
    # Add test entry
    entry = await store.store(
        key=test_entry["key"],
        content=test_entry["value"],
        scope=test_entry["scope"],
        metadata=test_entry["metadata"],
    )

    # Test deleting existing entry
    result = await store.delete("test1")
    assert result is True
    assert await store.exists("test1") is False

    # Test deleting non-existent entry
    result = await store.delete("non_existent")
    assert result is False


@pytest.mark.asyncio
async def test_store_exists(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test checking entry existence."""
    # Add test entry
    entry = await store.store(
        key=test_entry["key"],
        content=test_entry["value"],
        scope=test_entry["scope"],
        metadata=test_entry["metadata"],
    )

    # Test existing entry
    assert await store.exists("test1") is True

    # Test non-existent entry
    assert await store.exists("non_existent") is False


@pytest.mark.asyncio
async def test_store_clear(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test clearing entries."""
    # Add test entries with different scopes
    entries = {
        "test1": await store.store(
            key="test1",
            content=test_entry["value"],
            scope=MemoryScope.SESSION,
            metadata={"tags": "test"},
        ),
        "test2": await store.store(
            key="test2",
            content=test_entry["value"],
            scope=MemoryScope.AGENT,
            metadata={"tags": "test"},
        ),
    }

    # Test clearing all entries
    count = await store.clear()
    assert count == 2
    assert await store.exists("test1") is False
    assert await store.exists("test2") is False

    # Test clearing with scope filter
    entries = {
        "test1": await store.store(
            key="test1",
            content=test_entry["value"],
            scope=MemoryScope.SESSION,
            metadata={"tags": "test"},
        ),
        "test2": await store.store(
            key="test2",
            content=test_entry["value"],
            scope=MemoryScope.AGENT,
            metadata={"tags": "test"},
        ),
    }
    count = await store.clear(scope=MemoryScope.SESSION)
    assert count == 1
    assert await store.exists("test1") is False
    assert await store.exists("test2") is True


@pytest.mark.asyncio
async def test_store_search(store: InMemoryStore, test_entry: Dict[str, Any]) -> None:
    """Test search functionality."""
    # Add test entries
    entries = {
        "test1": await store.store(
            key="test1",
            content={"content": "This is a test document"},
            scope=test_entry["scope"],
            metadata={"tags": "test"},
        ),
        "test2": await store.store(
            key="test2",
            content={"content": "Another test document"},
            scope=test_entry["scope"],
            metadata={"tags": "test"},
        ),
        "test3": await store.store(
            key="test3",
            content={"content": "Completely different content"},
            scope=test_entry["scope"],
            metadata={"tags": "test"},
        ),
    }

    # Test basic search
    query = MemoryQuery(
        query="test",
        index_type=MemoryIndex.SEMANTIC,
        filters={},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)

    assert len(results) > 0
    assert results[0].key == "test1"
    assert "test" in str(results[0].entry["content"]).lower()

    # Test search with filters
    query = MemoryQuery(
        query="test",
        index_type=MemoryIndex.SEMANTIC,
        filters={"type": MemoryType.SHORT_TERM},
        metadata={},
    )
    results = []
    async for result in store.retrieve(query):
        results.append(result)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_store_concurrent_access(store: InMemoryStore) -> None:
    """Test concurrent access to the store."""

    async def write_entry(key: str, content: str) -> None:
        await store.store(
            key=key,
            content={"content": content},
            scope=MemoryScope.SESSION,
            metadata={"tags": "test"},
        )

    async def search_entries(query: str) -> List[MemoryResult[dict[str, Any]]]:
        results = []
        async for result in store.retrieve(
            MemoryQuery(
                query=query,
                index_type=MemoryIndex.SEMANTIC,
                filters={},
                metadata={},
            )
        ):
            results.append(result)
        return results

    # Test concurrent writes
    await asyncio.gather(*[write_entry(f"key{i}", f"content{i}") for i in range(10)])
    count = 0
    async for result in store.retrieve(
        MemoryQuery(
            query="",
            index_type=MemoryIndex.SEMANTIC,
            filters={},
            metadata={},
        )
    ):
        count += 1
    assert count == 10

    # Test concurrent searches
    results = await asyncio.gather(*[search_entries("test") for _ in range(5)])
    assert len(results) == 5
    assert all(isinstance(r, list) for r in results)
