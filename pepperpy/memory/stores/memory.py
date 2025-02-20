"""In-memory store implementation."""

from typing import Any, AsyncIterator, Dict, Optional

from pepperpy.core.protocols import MemoryScope
from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.memory.errors import MemoryError, MemoryKeyError


class InMemoryStore(BaseMemoryStore[Dict[str, Any]]):
    """In-memory store implementation."""

    def __init__(self, name: str = "memory", config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the store.

        Args:
            name: Store name
            config: Optional configuration
        """
        super().__init__(name=name)
        self._store: Dict[str, MemoryEntry[Dict[str, Any]]] = {}
        self._config = config or {}

    async def _initialize(self) -> None:
        """Initialize the store."""
        pass

    async def _cleanup(self) -> None:
        """Clean up resources."""
        self._store.clear()

    async def _store_entry(
        self,
        entry: MemoryEntry[Dict[str, Any]],
    ) -> MemoryEntry[Dict[str, Any]]:
        """Store an entry.

        Args:
            entry: Entry to store

        Returns:
            Stored entry

        Raises:
            MemoryError: If entry is invalid
        """
        if not entry.key:
            raise MemoryKeyError("Entry key cannot be empty")

        self._store[entry.key] = entry
        return entry

    async def _retrieve(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[Dict[str, Any]]]:
        """Retrieve entries matching query.

        Args:
            query: Query to match

        Yields:
            Matching entries

        Raises:
            MemoryError: If query is invalid
        """
        if not query.query:
            raise MemoryError("Query cannot be empty")

        for entry in self._store.values():
            if self._matches_query(entry, query):
                yield MemorySearchResult(
                    entry=entry,
                    score=1.0 if query.query == entry.key else 0.5,
                )

    async def _delete(self, key: str) -> bool:
        """Delete an entry.

        Args:
            key: Entry key

        Returns:
            True if deleted, False if not found
        """
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def _exists(self, key: str) -> bool:
        """Check if entry exists.

        Args:
            key: Entry key

        Returns:
            True if exists, False otherwise
        """
        return key in self._store

    async def _clear(self, scope: Optional[MemoryScope] = None) -> int:
        """Clear entries.

        Args:
            scope: Optional scope to clear

        Returns:
            Number of entries cleared
        """
        if scope is None:
            count = len(self._store)
            self._store.clear()
            return count

        count = 0
        keys_to_delete = []
        for key, entry in self._store.items():
            if entry.scope == scope:
                keys_to_delete.append(key)
                count += 1

        for key in keys_to_delete:
            del self._store[key]

        return count

    def _matches_query(
        self,
        entry: MemoryEntry[Dict[str, Any]],
        query: MemoryQuery,
    ) -> bool:
        """Check if entry matches query.

        Args:
            entry: Memory entry
            query: Memory query

        Returns:
            bool: True if matches, False otherwise
        """
        # Match key if specified
        if query.key and entry.key != query.key:
            return False

        # Match query text if specified
        if query.query:
            entry_text = str(entry.value).lower()
            if query.query.lower() not in entry_text:
                return False

        # Match filters if specified
        if query.filters:
            for key, value in query.filters.items():
                if key not in entry.value or entry.value[key] != value:
                    return False

        # Match metadata if specified
        if query.metadata:
            for key, value in query.metadata.items():
                if key not in entry.metadata or entry.metadata[key] != value:
                    return False

        return True
