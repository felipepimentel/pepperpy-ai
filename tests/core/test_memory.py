"""Tests for the Memory System.

This module contains tests for the Memory System, including:
- Memory store initialization and configuration
- Memory operations (store, retrieve, update, delete)
- Memory lifecycle management
- Memory error handling and validation
- Memory scope and backend management
"""

from typing import Any, Dict, Optional

import pytest

from pepperpy.core.memory.store import BaseMemoryStore
from pepperpy.core.types import MemoryBackend, MemoryScope


class TestMemoryStore(BaseMemoryStore):
    """Test implementation of BaseMemoryStore."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize test memory store."""
        super().__init__(config)
        self.scope = config.get("scope", MemoryScope.SESSION)
        self.backend = config.get("backend", MemoryBackend.DICT)
        self.store: Dict[str, Any] = {}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize memory store."""
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up memory store."""
        self.initialized = False
        self.store.clear()

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from memory."""
        if not self.initialized:
            raise RuntimeError("Memory store not initialized")
        return self.store.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Set a value in memory."""
        if not self.initialized:
            raise RuntimeError("Memory store not initialized")
        self.store[key] = value

    async def update(self, key: str, value: Any) -> None:
        """Update a value in memory."""
        if not self.initialized:
            raise RuntimeError("Memory store not initialized")
        if key not in self.store:
            raise KeyError(f"Key {key} not found")
        self.store[key] = value

    async def delete(self, key: str) -> None:
        """Delete a value from memory."""
        if not self.initialized:
            raise RuntimeError("Memory store not initialized")
        if key not in self.store:
            raise KeyError(f"Key {key} not found")
        del self.store[key]

    async def clear(self) -> None:
        """Clear all values from memory."""
        if not self.initialized:
            raise RuntimeError("Memory store not initialized")
        self.store.clear()

    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory."""
        if not self.initialized:
            raise RuntimeError("Memory store not initialized")
        return key in self.store


@pytest.fixture
def memory_store() -> TestMemoryStore:
    """Create a test memory store."""
    return TestMemoryStore({})


@pytest.mark.asyncio
async def test_memory_store_initialization():
    """Test memory store initialization."""
    store = TestMemoryStore({
        "scope": MemoryScope.GLOBAL,
        "backend": MemoryBackend.REDIS,
        "host": "localhost",
        "port": 6379,
    })

    assert store.scope == MemoryScope.GLOBAL
    assert store.backend == MemoryBackend.REDIS
    assert isinstance(store.config, dict)
    assert store.config["host"] == "localhost"
    assert store.config["port"] == 6379
    assert not store.initialized

    await store.initialize()
    assert store.initialized

    await store.cleanup()
    assert not store.initialized


@pytest.mark.asyncio
async def test_memory_store_operations(memory_store: TestMemoryStore):
    """Test memory store operations."""
    await memory_store.initialize()

    # Test store and retrieve
    key = "test_key"
    value = {"data": "test_value"}
    await memory_store.set(key, value)
    assert await memory_store.exists(key)
    assert await memory_store.get(key) == value

    # Test update
    new_value = {"data": "updated_value"}
    await memory_store.update(key, new_value)
    assert await memory_store.get(key) == new_value

    # Test delete
    await memory_store.delete(key)
    assert not await memory_store.exists(key)
    assert await memory_store.get(key) is None

    # Test clear
    await memory_store.set("key1", "value1")
    await memory_store.set("key2", "value2")
    assert await memory_store.exists("key1")
    assert await memory_store.exists("key2")
    await memory_store.clear()
    assert not await memory_store.exists("key1")
    assert not await memory_store.exists("key2")


@pytest.mark.asyncio
async def test_memory_store_error_handling():
    """Test memory store error handling."""
    store = TestMemoryStore({})

    # Test operations before initialization
    with pytest.raises(RuntimeError, match="Memory store not initialized"):
        await store.set("key", "value")

    with pytest.raises(RuntimeError, match="Memory store not initialized"):
        await store.get("key")

    with pytest.raises(RuntimeError, match="Memory store not initialized"):
        await store.update("key", "value")

    with pytest.raises(RuntimeError, match="Memory store not initialized"):
        await store.delete("key")

    with pytest.raises(RuntimeError, match="Memory store not initialized"):
        await store.clear()

    with pytest.raises(RuntimeError, match="Memory store not initialized"):
        await store.exists("key")

    # Initialize store and test invalid operations
    await store.initialize()

    # Test update non-existent key
    with pytest.raises(KeyError, match="Key test_key not found"):
        await store.update("test_key", "value")

    # Test delete non-existent key
    with pytest.raises(KeyError, match="Key test_key not found"):
        await store.delete("test_key")


@pytest.mark.asyncio
async def test_memory_store_scope_isolation():
    """Test memory store scope isolation."""
    session_store = TestMemoryStore({"scope": MemoryScope.SESSION})
    agent_store = TestMemoryStore({"scope": MemoryScope.AGENT})
    global_store = TestMemoryStore({"scope": MemoryScope.GLOBAL})

    await session_store.initialize()
    await agent_store.initialize()
    await global_store.initialize()

    # Store values in different scopes
    await session_store.set("key", "session_value")
    await agent_store.set("key", "agent_value")
    await global_store.set("key", "global_value")

    # Verify scope isolation
    assert await session_store.get("key") == "session_value"
    assert await agent_store.get("key") == "agent_value"
    assert await global_store.get("key") == "global_value"

    # Clear session scope
    await session_store.clear()
    assert await session_store.get("key") is None
    assert await agent_store.get("key") == "agent_value"
    assert await global_store.get("key") == "global_value"


@pytest.mark.asyncio
async def test_memory_store_backend_configuration():
    """Test memory store backend configuration."""
    # Test Dict backend
    dict_store = TestMemoryStore({"backend": MemoryBackend.DICT})
    assert dict_store.backend == MemoryBackend.DICT
    await dict_store.initialize()
    await dict_store.set("key", "value")
    assert await dict_store.get("key") == "value"

    # Test Redis backend configuration
    redis_store = TestMemoryStore({
        "backend": MemoryBackend.REDIS,
        "host": "localhost",
        "port": 6379,
        "db": 0,
    })
    assert redis_store.backend == MemoryBackend.REDIS
    assert isinstance(redis_store.config, dict)
    assert redis_store.config["host"] == "localhost"
    assert redis_store.config["port"] == 6379

    # Test SQLite backend configuration
    sqlite_store = TestMemoryStore({
        "backend": MemoryBackend.SQLITE,
        "path": ":memory:",
        "table": "memory",
    })
    assert sqlite_store.backend == MemoryBackend.SQLITE
    assert isinstance(sqlite_store.config, dict)
    assert sqlite_store.config["path"] == ":memory:"
    assert sqlite_store.config["table"] == "memory"


@pytest.mark.asyncio
async def test_memory_store_concurrent_operations(memory_store: TestMemoryStore):
    """Test memory store concurrent operations."""
    await memory_store.initialize()

    # Test concurrent store operations
    import asyncio

    keys = [f"key_{i}" for i in range(10)]
    values = [f"value_{i}" for i in range(10)]

    await asyncio.gather(*[
        memory_store.set(key, value) for key, value in zip(keys, values, strict=False)
    ])

    # Verify all values were stored
    results = await asyncio.gather(*[memory_store.get(key) for key in keys])

    assert all(value in results for value in values)

    # Test concurrent updates
    new_values = [f"new_value_{i}" for i in range(10)]
    await asyncio.gather(*[
        memory_store.update(key, value)
        for key, value in zip(keys, new_values, strict=False)
    ])

    # Verify all values were updated
    results = await asyncio.gather(*[memory_store.get(key) for key in keys])

    assert all(value in results for value in new_values)
