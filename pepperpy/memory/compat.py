"""Backward compatibility layer for memory system.

This module provides compatibility wrappers to maintain the old memory system
interface while using the new implementation underneath.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Generic, TypeVar, cast
from uuid import UUID

from pepperpy.memory.store import BaseMemoryStore
from pepperpy.memory.types import (
    MemoryEntry as NewMemoryEntry,
)
from pepperpy.memory.types import (
    MemoryIndex,
)
from pepperpy.memory.types import (
    MemoryQuery as NewMemoryQuery,
)
from pepperpy.memory.types import (
    MemoryResult as NewMemoryResult,
)
from pepperpy.memory.types import (
    MemoryScope as NewMemoryScope,
)
from pepperpy.memory.types import (
    MemoryType as NewMemoryType,
)

# Type variables for generic parameters
K = TypeVar("K", str, UUID)  # Key type
T = TypeVar("T", bound=dict[str, Any])  # Store value type
V = TypeVar("V", bound=dict[str, Any])  # Memory entry value type


class MemoryEntry(Generic[V]):
    """Memory entry model."""

    def __init__(
        self,
        key: str,
        value: V,
        type: str = NewMemoryType.SHORT_TERM,
        scope: str = NewMemoryScope.SESSION,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        expires_at: datetime | None = None,
        indices: set[str] | None = None,
    ) -> None:
        """Initialize memory entry."""
        self.key = key
        self.value = value
        self.type = type
        self.scope = scope
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.expires_at = expires_at
        self.indices = indices or set()


def _convert_type(old_type: str | None) -> NewMemoryType:
    """Convert old memory type to new format."""
    if not old_type:
        return NewMemoryType.SHORT_TERM
    return NewMemoryType(old_type)


def _convert_scope(old_scope: str | None) -> NewMemoryScope:
    """Convert old memory scope to new format."""
    if not old_scope:
        return NewMemoryScope.SESSION
    return NewMemoryScope(old_scope)


def _convert_to_new_entry(entry: MemoryEntry[V]) -> NewMemoryEntry[V]:
    """Convert old memory entry to new format."""
    return NewMemoryEntry[V](
        key=entry.key,
        value=entry.value,
        type=_convert_type(entry.type),
        scope=_convert_scope(entry.scope),
        metadata=entry.metadata,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        expires_at=entry.expires_at,
        indices=entry.indices,
    )


def _convert_to_old_entry(entry: NewMemoryEntry[V]) -> MemoryEntry[V]:
    """Convert new memory entry to old format."""
    return MemoryEntry[V](
        key=entry.key,
        value=entry.value,
        type=str(entry.type),
        scope=str(entry.scope),
        metadata=entry.metadata,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        expires_at=entry.expires_at,
        indices=entry.indices,
    )


class BaseMemory(Generic[K, V]):
    """Legacy base memory interface."""

    def __init__(self) -> None:
        """Initialize base memory."""
        self._store: BaseMemoryStore[V] | None = None

    def _check_store(self) -> BaseMemoryStore[V]:
        """Check if store is initialized."""
        if self._store is None:
            raise RuntimeError("Memory store not initialized")
        return self._store

    async def search(
        self,
        query: str,
        type: str | None = None,
        scope: str | None = None,
    ) -> AsyncGenerator[NewMemoryResult[V], None]:
        """Search memory entries."""
        try:
            store = self._check_store()
            memory_query = NewMemoryQuery(
                query=query,
                index_type=MemoryIndex.SEMANTIC,
                filters=(
                    {}
                    if not type and not scope
                    else {
                        **({"type": _convert_type(type)} if type else {}),
                        **({"scope": _convert_scope(scope)} if scope else {}),
                    }
                ),
            )

            async for result in store.retrieve(memory_query):
                # Convert the entry to the correct type
                old_entry = _convert_to_old_entry(cast(NewMemoryEntry[V], result.entry))
                yield NewMemoryResult[V](
                    key=result.key,
                    entry=old_entry.value,  # Use the value from the old entry
                    similarity=result.similarity,
                    metadata=result.metadata,
                )

        except Exception as e:
            raise RuntimeError(f"Failed to search memory entries: {e}") from e

    async def list(
        self,
        type: str | None = None,
        scope: str | None = None,
        pattern: str | None = None,
    ) -> AsyncGenerator[MemoryEntry[V], None]:
        """List memory entries."""
        try:
            store = self._check_store()
            memory_query = NewMemoryQuery(
                query=pattern or "",
                index_type=MemoryIndex.SEMANTIC,
                filters=(
                    {}
                    if not type and not scope
                    else {
                        **({"type": _convert_type(type)} if type else {}),
                        **({"scope": _convert_scope(scope)} if scope else {}),
                    }
                ),
            )

            async for result in store.retrieve(memory_query):
                yield _convert_to_old_entry(cast(NewMemoryEntry[V], result.entry))

        except Exception as e:
            raise RuntimeError(f"Failed to list memory entries: {e}") from e


class CompatMemoryStore(BaseMemory[K, V]):
    """Compatibility wrapper for new memory store implementation."""

    def __init__(self, store: BaseMemoryStore[V]) -> None:
        """Initialize the compatibility wrapper."""
        super().__init__()
        self._store = store
        self._lock = asyncio.Lock()

    async def store(
        self,
        key: K,
        value: V,
        type: str = NewMemoryType.SHORT_TERM,
        scope: str = NewMemoryScope.SESSION,
        metadata: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
        indices: set[str] | None = None,
    ) -> MemoryEntry[V]:
        """Store a memory entry."""
        try:
            store = self._check_store()
            new_scope = _convert_scope(scope)

            # Create entry in old format first
            old_entry = MemoryEntry(
                key=str(key),
                value=value,
                type=type,
                scope=scope,
                metadata=metadata,
                expires_at=expires_at,
                indices=indices,
            )

            # Convert to new format and store
            new_entry = _convert_to_new_entry(old_entry)
            stored_entry = await store.store(
                str(key),
                new_entry.value,
                new_scope,
                metadata,
            )

            # Convert back to old format
            return _convert_to_old_entry(stored_entry)

        except Exception as e:
            raise RuntimeError(f"Failed to store memory entry: {e}") from e

    async def retrieve(
        self,
        key: K,
        type: str | None = None,
    ) -> MemoryEntry[V]:
        """Retrieve a memory entry."""
        try:
            store = self._check_store()
            memory_query = NewMemoryQuery(
                query="",  # Empty query for direct key lookup
                index_type=MemoryIndex.SEMANTIC,
                filters={} if not type else {"type": _convert_type(type)},
                metadata={"key": str(key)},
            )

            async for result in store.retrieve(memory_query):
                # Cast to NewMemoryEntry[V] since type inference needs help here
                entry = cast(NewMemoryEntry[V], result.entry)
                return _convert_to_old_entry(entry)

            raise KeyError(f"Memory key not found: {key}")

        except Exception as e:
            if isinstance(e, KeyError):
                raise
            raise RuntimeError(f"Failed to retrieve memory entry: {e}") from e

    async def reindex(
        self,
        index: str,
        keys: list[K] | None = None,
    ) -> int:
        """Reindex memory entries."""
        try:
            store = self._check_store()
            # Create query for entries to reindex
            query = NewMemoryQuery(
                query="",
                index_type=MemoryIndex.SEMANTIC,
                metadata={},
                min_score=0.0,  # Not used for reindexing
                limit=1000,  # High limit for reindexing
            )

            # Reindex entries
            count = 0
            async for result in store.retrieve(query):
                if keys and str(result.key) not in [str(k) for k in keys]:
                    continue

                # Re-store entry to trigger reindexing
                entry = cast(NewMemoryEntry[V], result.entry)
                await store.store(
                    result.key,
                    entry.value,  # Use the value directly from the entry
                    _convert_scope(entry.scope),
                    entry.metadata,
                )
                count += 1

            return count

        except Exception as e:
            raise RuntimeError(f"Failed to reindex memory entries: {e}") from e

    async def _convert_query(self, query: NewMemoryQuery) -> NewMemoryQuery:
        """Convert memory query to new format.

        Args:
            query: Memory query to convert

        Returns:
            Converted memory query
        """
        return NewMemoryQuery(
            query=query.query,
            index_type=MemoryIndex.SEMANTIC,
            filters=query.filters,
            metadata=query.metadata,
            min_score=query.min_score,
            limit=query.limit,
            offset=query.offset,
            order_by=query.order_by,
            order=query.order,
            key=query.key,
            keys=query.keys,
        )
