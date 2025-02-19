"""@file: memory.py
@purpose: Runtime memory management system
@component: Runtime
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Generic, Optional, TypeVar
from uuid import UUID, uuid4

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger
from pepperpy.core.types import JSON
from pepperpy.runtime.context import get_current_context
from pepperpy.runtime.lifecycle import get_lifecycle_manager

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class MemoryConfig:
    """Configuration for memory management."""

    enabled: bool = True
    max_size: int = 10000
    ttl: float = 3600.0  # Time to live in seconds
    cleanup_interval: float = 300.0  # Cleanup interval in seconds

    def validate(self) -> None:
        """Validate memory configuration."""
        if self.max_size < 1:
            raise ConfigurationError("Max size must be positive")
        if self.ttl <= 0:
            raise ConfigurationError("TTL must be positive")
        if self.cleanup_interval <= 0:
            raise ConfigurationError("Cleanup interval must be positive")


@dataclass
class Memory(Generic[T]):
    """Memory entry for storing data with metadata."""

    key: str
    value: T
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> JSON:
        """Convert memory entry to JSON format."""
        return {
            "id": str(self.id),
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }


class MemoryStore(Generic[T]):
    """Storage for memory entries."""

    def __init__(self) -> None:
        """Initialize memory store."""
        self._entries: Dict[str, Memory[T]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Memory[T]]:
        """Get a memory entry by key.

        Args:
            key: Memory key

        Returns:
            Memory entry if found and not expired

        """
        with self._lock:
            entry = self._entries.get(key)
            if entry and self._is_expired(entry):
                del self._entries[key]
                return None
            return entry

    def set(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory[T]:
        """Set a memory entry.

        Args:
            key: Memory key
            value: Value to store
            ttl: Optional time to live in seconds
            metadata: Optional metadata

        Returns:
            Created memory entry

        """
        now = datetime.utcnow()
        expires = now + timedelta(seconds=ttl) if ttl else None
        entry = Memory(
            key=key,
            value=value,
            created_at=now,
            updated_at=now,
            expires_at=expires,
            metadata=metadata or {},
        )
        with self._lock:
            self._entries[key] = entry
        return entry

    def delete(self, key: str) -> None:
        """Delete a memory entry.

        Args:
            key: Memory key

        """
        with self._lock:
            if key in self._entries:
                del self._entries[key]

    def cleanup(self) -> None:
        """Clean up expired entries."""
        with self._lock:
            for key in list(self._entries.keys()):
                entry = self._entries[key]
                if self._is_expired(entry):
                    del self._entries[key]

    def _is_expired(self, entry: Memory[T]) -> bool:
        """Check if a memory entry is expired.

        Args:
            entry: Memory entry to check

        Returns:
            Whether the entry is expired

        """
        return bool(entry.expires_at and entry.expires_at <= datetime.utcnow())


class MemoryManager:
    """Manager for runtime memory."""

    def __init__(self, config: Optional[MemoryConfig] = None) -> None:
        """Initialize memory manager.

        Args:
            config: Optional memory configuration

        """
        self.config = config or MemoryConfig()
        self.config.validate()

        self._stores: Dict[str, MemoryStore[Any]] = {}
        self._lock = threading.Lock()
        self._lifecycle = get_lifecycle_manager().create(
            context=get_current_context(),
            metadata={"component": "memory_manager"},
        )

    def get_store(self, name: str) -> MemoryStore[Any]:
        """Get a memory store by name.

        Args:
            name: Store name

        Returns:
            Memory store instance

        """
        with self._lock:
            if name not in self._stores:
                self._stores[name] = MemoryStore()
            return self._stores[name]

    def cleanup(self) -> None:
        """Clean up all memory stores."""
        with self._lock:
            for store in self._stores.values():
                store.cleanup()


class MemoryProvider:
    """Provider for memory store registration and lookup."""

    def __init__(self) -> None:
        """Initialize memory provider."""
        self._stores: Dict[str, MemoryStore[Any]] = {}
        self._lock = threading.Lock()

    def register(self, name: str, store: MemoryStore[Any]) -> None:
        """Register a memory store.

        Args:
            name: Store name
            store: Memory store instance

        """
        with self._lock:
            self._stores[name] = store

    def unregister(self, name: str) -> None:
        """Unregister a memory store.

        Args:
            name: Store name

        """
        with self._lock:
            if name in self._stores:
                del self._stores[name]

    def get(self, name: str) -> Optional[MemoryStore[Any]]:
        """Get a memory store by name.

        Args:
            name: Store name

        Returns:
            Memory store if found, None otherwise

        """
        return self._stores.get(name)


# Global instances
_memory_manager = MemoryManager()
_memory_provider = MemoryProvider()


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager.

    Returns:
        Global memory manager instance

    """
    return _memory_manager
