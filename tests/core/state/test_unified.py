"""Tests for the unified state management system."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

from pepperpy.core.memory.unified import MemoryEntry, MemoryStore
from pepperpy.core.state.unified import (
    BaseStateManager,
    PersistentStateManager,
    SharedStateManager,
    StateEntry,
    StateType,
)


def test_state_type():
    """Test state type enumeration."""
    assert StateType.EPHEMERAL.value == "ephemeral"
    assert StateType.PERSISTENT.value == "persistent"
    assert StateType.SHARED.value == "shared"


def test_state_entry():
    """Test state entry creation and conversion."""
    entry = StateEntry(
        key="test",
        value="test value",
        type=StateType.EPHEMERAL,
        metadata={"type": "test"},
        version=1,
    )

    assert entry.key == "test"
    assert entry.value == "test value"
    assert entry.type == StateType.EPHEMERAL
    assert entry.metadata == {"type": "test"}
    assert entry.version == 1

    # Test dictionary conversion
    entry_dict = entry.to_dict()
    assert entry_dict["key"] == "test"
    assert entry_dict["value"] == "test value"
    assert entry_dict["type"] == "ephemeral"
    assert entry_dict["metadata"] == {"type": "test"}
    assert entry_dict["version"] == 1
    assert "created_at" in entry_dict
    assert "updated_at" in entry_dict


class TestBaseStateManager:
    """Tests for the base state manager."""

    @pytest.fixture
    def manager(self) -> BaseStateManager[str]:
        """Fixture providing a base state manager."""
        return BaseStateManager()

    @pytest.mark.asyncio
    async def test_set_and_get(self, manager):
        """Test setting and getting state."""
        await manager.set("key1", "value1")
        value = await manager.get("key1")

        assert value == "value1"
        assert await manager.exists("key1")

    @pytest.mark.asyncio
    async def test_get_default(self, manager):
        """Test getting non-existent state."""
        value = await manager.get("nonexistent", default="default")
        assert value == "default"

    @pytest.mark.asyncio
    async def test_set_with_metadata(self, manager):
        """Test setting state with metadata."""
        await manager.set(
            "key1", "value1", type=StateType.PERSISTENT, metadata={"type": "test"}
        )

        entry = manager._store["key1"]
        assert entry.type == StateType.PERSISTENT
        assert entry.metadata == {"type": "test"}

    @pytest.mark.asyncio
    async def test_delete(self, manager):
        """Test deleting state."""
        await manager.set("key1", "value1")
        assert await manager.exists("key1")

        # Delete existing key
        assert await manager.delete("key1")
        assert not await manager.exists("key1")

        # Delete non-existent key
        assert not await manager.delete("key2")

    @pytest.mark.asyncio
    async def test_list(self, manager):
        """Test listing state keys."""
        # Add test data
        await manager.set("prefix1:a", "value1", type=StateType.EPHEMERAL)
        await manager.set("prefix1:b", "value2", type=StateType.PERSISTENT)
        await manager.set("prefix2:a", "value3", type=StateType.SHARED)

        # List all keys
        keys = await manager.list()
        assert len(keys) == 3
        assert "prefix1:a" in keys
        assert "prefix1:b" in keys
        assert "prefix2:a" in keys

        # List with pattern
        keys = await manager.list("prefix1:")
        assert len(keys) == 2
        assert all(key.startswith("prefix1:") for key in keys)

        # List with type
        keys = await manager.list(type=StateType.PERSISTENT)
        assert len(keys) == 1
        assert "prefix1:b" in keys


class TestPersistentStateManager:
    """Tests for the persistent state manager."""

    class TestMemoryStore(MemoryStore[str]):
        """Test memory store implementation."""

        def __init__(self):
            """Initialize the test store."""
            self._entries: dict[str, MemoryEntry[str]] = {}

        async def get(self, key: str) -> MemoryEntry[str] | None:
            """Get entry by key."""
            return self._entries.get(key)

        async def set(
            self, key: str, value: str, metadata: dict[str, Any] | None = None
        ) -> None:
            """Set entry value."""
            self._entries[key] = MemoryEntry(key=key, value=value, metadata=metadata)

        async def delete(self, key: str) -> bool:
            """Delete entry by key."""
            if key in self._entries:
                del self._entries[key]
                return True
            return False

        async def scan(self, pattern: str | None = None) -> AsyncIterator[str]:
            """Scan keys."""
            for key in self._entries:
                if not pattern or pattern in key:
                    yield key

    @pytest.fixture
    def store(self) -> TestMemoryStore:
        """Fixture providing a test memory store."""
        return TestMemoryStore()

    @pytest.fixture
    def manager(self, store) -> PersistentStateManager[str]:
        """Fixture providing a persistent state manager."""
        return PersistentStateManager(store)

    @pytest.mark.asyncio
    async def test_set_and_get(self, manager):
        """Test setting and getting state."""
        await manager.set("key1", "value1")
        value = await manager.get("key1")

        assert value == "value1"
        assert await manager.exists("key1")

    @pytest.mark.asyncio
    async def test_set_with_metadata(self, manager):
        """Test setting state with metadata."""
        await manager.set(
            "key1", "value1", type=StateType.PERSISTENT, metadata={"type": "test"}
        )

        entry = await manager._store.get("key1")
        assert entry is not None
        assert entry.metadata["state_type"] == "persistent"
        assert entry.metadata["type"] == "test"

    @pytest.mark.asyncio
    async def test_list(self, manager):
        """Test listing state keys."""
        # Add test data
        await manager.set("prefix1:a", "value1", type=StateType.PERSISTENT)
        await manager.set("prefix1:b", "value2", type=StateType.PERSISTENT)
        await manager.set("prefix2:a", "value3", type=StateType.SHARED)

        # List all keys
        keys = await manager.list()
        assert len(keys) == 3

        # List with pattern
        keys = await manager.list("prefix1:")
        assert len(keys) == 2

        # List with type
        keys = await manager.list(type=StateType.PERSISTENT)
        assert len(keys) == 2


class TestSharedStateManager:
    """Tests for the shared state manager."""

    @pytest.fixture
    def manager(self) -> SharedStateManager[str]:
        """Fixture providing a shared state manager."""
        return SharedStateManager()

    @pytest.mark.asyncio
    async def test_subscribe_and_notify(self, manager):
        """Test state change notifications."""
        # Subscribe to state changes
        queue = await manager.subscribe("key1")

        # Set state value
        await manager.set("key1", "value1")

        # Get notification
        entry = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert entry.key == "key1"
        assert entry.value == "value1"
        assert entry.type == StateType.SHARED

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, manager):
        """Test multiple subscribers to same key."""
        # Subscribe multiple queues
        queue1 = await manager.subscribe("key1")
        queue2 = await manager.subscribe("key1")

        # Set state value
        await manager.set("key1", "value1")

        # Both queues should receive notification
        entry1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
        entry2 = await asyncio.wait_for(queue2.get(), timeout=1.0)

        assert entry1.value == "value1"
        assert entry2.value == "value1"

    @pytest.mark.asyncio
    async def test_unsubscribe(self, manager):
        """Test unsubscribing from state changes."""
        # Subscribe and then unsubscribe
        queue = await manager.subscribe("key1")
        await manager.unsubscribe("key1", queue)

        # Set state value
        await manager.set("key1", "value1")

        # Queue should be empty
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.1)
