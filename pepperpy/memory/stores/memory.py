"""In-memory store implementation."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
    MemoryType,
)
from pepperpy.memory.errors import MemoryKeyError


class InMemoryStore(BaseMemoryStore[Dict[str, Any]]):
    """In-memory store implementation."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize in-memory store.

        Args:
            name: Store name
            config: Store configuration

        """
        super().__init__(name=name)
        self._store: Dict[str, MemoryEntry[Dict[str, Any]]] = {}
        self._config = config or {}

    async def _initialize(self) -> None:
        """Initialize the store."""
        pass  # No initialization needed for in-memory store

    async def _cleanup(self) -> None:
        """Clean up the store."""
        self._store.clear()

    async def _store_entry(self, entry: MemoryEntry[Dict[str, Any]]) -> None:
        """Store a memory entry.

        Args:
            entry: Memory entry to store

        Raises:
            MemoryKeyError: If key is invalid

        """
        if not entry.key:
            raise MemoryKeyError("Key cannot be empty")
        self._store[entry.key] = entry

    async def _retrieve(
        self, query: MemoryQuery
    ) -> AsyncIterator[MemorySearchResult[Dict[str, Any]]]:
        """Retrieve memory entries.

        Args:
            query: Memory query

        Yields:
            Memory search results

        """
        if query.key:
            if query.key in self._store:
                entry = self._store[query.key]
                yield MemorySearchResult(
                    entry=entry,
                    score=1.0,  # Exact match
                    metadata={},
                )
            return

        for entry in self._store.values():
            # Simple substring search for demo
            if query.query.lower() in str(entry.value).lower():
                yield MemorySearchResult(
                    entry=entry,
                    score=1.0,  # Simple match score
                    metadata={},
                )

    async def _delete(self, key: str) -> None:
        """Delete a memory entry.

        Args:
            key: Key to delete

        Raises:
            MemoryKeyError: If key not found

        """
        if key not in self._store:
            raise MemoryKeyError(f"Key not found: {key}")
        del self._store[key]

    async def store(
        self,
        key: str,
        value: Dict[str, Any],
        type: MemoryType = MemoryType.SHORT_TERM,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> MemoryEntry:
        """Store a value in memory.

        Args:
            key: Key to store value under
            value: Value to store
            type: Type of memory
            metadata: Optional metadata
            expires_at: Optional expiration time

        Returns:
            Memory entry

        """
        entry = MemoryEntry(
            key=key,
            value=value,
            type=type,
            metadata=metadata or {},
            expires_at=expires_at,
            created_at=datetime.now(UTC),
        )
        self._store[key] = entry
        return entry

    async def retrieve(
        self,
        key: str,
        type: Optional[MemoryType] = None,
    ) -> MemoryEntry:
        """Retrieve a value from memory.

        Args:
            key: Key to retrieve
            type: Optional type filter

        Returns:
            Memory entry

        Raises:
            MemoryKeyError: If key not found

        """
        if key not in self._store:
            raise MemoryKeyError(f"Key not found: {key}")

        entry = self._store[key]

        if type is not None and entry.type != type:
            raise MemoryKeyError(f"Key {key} has wrong type: {entry.type} != {type}")

        return entry

    async def search(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult]:
        """Search memory entries.

        Args:
            query: Search query

        Yields:
            Memory search results

        """
        for entry in self._store.values():
            # Simple substring search for demo
            if query.query.lower() in str(entry.value).lower():
                yield MemorySearchResult(
                    entry=entry,
                    score=1.0,  # Simple exact match score
                    metadata={},
                )

    async def cleanup(self) -> None:
        """Clean up expired entries."""
        now = datetime.now(UTC)
        expired = [
            key
            for key, entry in self._store.items()
            if entry.expires_at and entry.expires_at <= now
        ]
        for key in expired:
            del self._store[key]
