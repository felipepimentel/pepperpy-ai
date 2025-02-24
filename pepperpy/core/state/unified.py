"""Unified state management system for Pepperpy.

This module provides a comprehensive state management framework that includes:
- State type classification
- State entry representation
- Abstract state manager interface
- Base state manager implementation
- Persistent state manager implementation
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pepperpy.core.errors.unified import PepperpyError
from pepperpy.core.memory.unified import MemoryStore
from pepperpy.core.metrics import MetricsManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class StateError(PepperpyError):
    """Base class for state-related errors."""

    def __init__(self, message: str, code: str = "STATE000", **kwargs):
        super().__init__(message, code=code, category="state", **kwargs)


class StateType(Enum):
    """State entry types."""

    EPHEMERAL = "ephemeral"  # Temporary state
    PERSISTENT = "persistent"  # Persistent state
    SHARED = "shared"  # Shared state


@dataclass
class StateEntry(Generic[T]):
    """Represents a state entry with metadata."""

    key: str
    value: T
    type: StateType
    metadata: dict[str, Any] | None = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert the state entry to a dictionary.

        Returns:
            Dictionary containing the entry data.
        """
        return {
            "key": self.key,
            "value": self.value,
            "type": self.type.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }


class StateManager(ABC, Generic[T]):
    """Abstract base class for state managers."""

    @abstractmethod
    async def get(self, key: str, default: T | None = None) -> T | None:
        """Get state value by key.

        Args:
            key: The state key.
            default: Default value if key not found.

        Returns:
            The state value if found, default otherwise.
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: T,
        type: StateType = StateType.EPHEMERAL,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set state value.

        Args:
            key: The state key.
            value: The state value.
            type: The state type.
            metadata: Optional metadata.
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete state by key.

        Args:
            key: The state key.

        Returns:
            True if state was deleted, False if not found.
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if state exists.

        Args:
            key: The state key.

        Returns:
            True if state exists, False otherwise.
        """
        pass

    @abstractmethod
    async def list(
        self, pattern: str | None = None, type: StateType | None = None
    ) -> list[str]:
        """List state keys matching pattern and type.

        Args:
            pattern: Optional key pattern to match.
            type: Optional state type to match.

        Returns:
            List of matching state keys.
        """
        pass


class BaseStateManager(StateManager[T]):
    """Base implementation of state manager with common functionality."""

    def __init__(self):
        """Initialize the base state manager."""
        self._metrics = MetricsManager.get_instance()
        self._lock = asyncio.Lock()
        self._store: dict[str, StateEntry[T]] = {}

    async def exists(self, key: str) -> bool:
        """Check if state exists."""
        async with self._lock:
            return key in self._store

    async def get(self, key: str, default: T | None = None) -> T | None:
        """Get state value by key."""
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                await self._record_operation("get", False, reason="not_found")
                return default

            await self._record_operation("get", True)
            return entry.value

    async def set(
        self,
        key: str,
        value: T,
        type: StateType = StateType.EPHEMERAL,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set state value."""
        async with self._lock:
            existing = self._store.get(key)
            version = existing.version + 1 if existing else 1

            entry = StateEntry(
                key=key,
                value=value,
                type=type,
                metadata=metadata,
                updated_at=datetime.now(),
                version=version,
            )

            self._store[key] = entry
            await self._record_operation("set", True)

    async def delete(self, key: str) -> bool:
        """Delete state by key."""
        async with self._lock:
            if key not in self._store:
                await self._record_operation("delete", False, reason="not_found")
                return False

            del self._store[key]
            await self._record_operation("delete", True)
            return True

    async def list(
        self, pattern: str | None = None, type: StateType | None = None
    ) -> list[str]:
        """List state keys matching pattern and type."""
        async with self._lock:
            keys = []
            for key, entry in self._store.items():
                if pattern and not key.startswith(pattern):
                    continue
                if type and entry.type != type:
                    continue
                keys.append(key)
            return keys

    async def _record_operation(
        self, operation: str, success: bool = True, **labels: str
    ) -> None:
        """Record a state operation metric.

        Args:
            operation: The operation name.
            success: Whether the operation succeeded.
            **labels: Additional metric labels.
        """
        self._metrics.counter(
            f"state_manager_{operation}", 1, success=str(success).lower(), **labels
        )


class PersistentStateManager(BaseStateManager[T]):
    """State manager implementation using persistent storage."""

    def __init__(self, store: MemoryStore[T]):
        """Initialize the persistent state manager.

        Args:
            store: The memory store to use for persistence.
        """
        super().__init__()
        self._store = store

    async def get(self, key: str, default: T | None = None) -> T | None:
        """Get state value by key."""
        entry = await self._store.get(key)
        if entry is None:
            await self._record_operation("get", False, reason="not_found")
            return default

        await self._record_operation("get", True)
        return entry.value

    async def set(
        self,
        key: str,
        value: T,
        type: StateType = StateType.PERSISTENT,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set state value."""
        await self._store.set(
            key, value, metadata={**(metadata or {}), "state_type": type.value}
        )
        await self._record_operation("set", True)

    async def delete(self, key: str) -> bool:
        """Delete state by key."""
        try:
            await self._store.delete(key)
            await self._record_operation("delete", True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete state: {e}", extra={"key": key})
            await self._record_operation("delete", False, reason="error")
            return False

    async def list(
        self, pattern: str | None = None, type: StateType | None = None
    ) -> list[str]:
        """List state keys matching pattern and type."""
        keys = []
        async for key in self._store.scan(pattern):
            if type:
                entry = await self._store.get(key)
                if entry is None:
                    continue
                if entry.metadata.get("state_type") != type.value:
                    continue
            keys.append(key)
        return keys


class SharedStateManager(BaseStateManager[T]):
    """State manager implementation for shared state."""

    def __init__(self):
        """Initialize the shared state manager."""
        super().__init__()
        self._subscribers: dict[str, list[asyncio.Queue[StateEntry[T]]]] = {}

    async def set(
        self,
        key: str,
        value: T,
        type: StateType = StateType.SHARED,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set state value and notify subscribers."""
        await super().set(key, value, type, metadata)

        # Notify subscribers
        if key in self._subscribers:
            entry = self._store[key]
            for queue in self._subscribers[key]:
                await queue.put(entry)

    async def subscribe(self, key: str) -> asyncio.Queue[StateEntry[T]]:
        """Subscribe to state changes.

        Args:
            key: The state key to subscribe to.

        Returns:
            Queue that will receive state updates.
        """
        if key not in self._subscribers:
            self._subscribers[key] = []

        queue: asyncio.Queue[StateEntry[T]] = asyncio.Queue()
        self._subscribers[key].append(queue)
        return queue

    async def unsubscribe(self, key: str, queue: asyncio.Queue[StateEntry[T]]) -> None:
        """Unsubscribe from state changes.

        Args:
            key: The state key to unsubscribe from.
            queue: The queue to remove.
        """
        if key in self._subscribers:
            self._subscribers[key].remove(queue)
