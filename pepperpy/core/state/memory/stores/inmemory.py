"""In-memory store implementation.

Simple in-memory store for storing and retrieving memory entries.
Useful for testing and development purposes.
"""

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, AsyncIterator, Dict

from pepperpy.core.logging import get_logger
from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemoryScope,
    MemoryType,
)
from pepperpy.memory.errors import MemoryError, MemoryKeyError
from pepperpy.memory.types import MemoryResult

# Configure logger
logger = get_logger(__name__)


class InMemoryStore(BaseMemoryStore[dict[str, Any]]):
    """In-memory store implementation."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the in-memory store.

        Args:
        ----
            config: Store configuration

        """
        self.config = config
        self._entries: dict[str, MemoryEntry[dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the memory store."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        async with self._lock:
            self._entries.clear()

    async def get(self, key: str) -> MemoryEntry[dict[str, Any]] | None:
        """Get an entry by key.

        Args:
        ----
            key: Key to retrieve

        Returns:
        -------
            Entry if found, None otherwise

        """
        async with self._lock:
            return self._entries.get(key)

    async def set(
        self,
        key: str,
        value: dict[str, Any],
        scope: MemoryScope = MemoryScope.SESSION,
        metadata: dict[str, str] | None = None,
    ) -> MemoryEntry[dict[str, Any]]:
        """Set an entry.

        Args:
        ----
            key: Key to store under
            value: Value to store
            scope: Storage scope
            metadata: Optional metadata

        Returns:
        -------
            Created memory entry

        """
        return await self._store_impl(key, value, scope, metadata)

    async def delete(self, key: str) -> bool:
        """Delete an entry.

        Args:
        ----
            key: Key to delete

        Returns:
        -------
            True if deleted, False if not found

        """
        return await self._delete_impl(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
        ----
            key: Key to check

        Returns:
        -------
            True if exists, False otherwise

        """
        return await self._exists_impl(key)

    async def clear(self, scope: MemoryScope | None = None) -> int:
        """Clear entries.

        Args:
        ----
            scope: Optional scope to clear

        Returns:
        -------
            Number of entries cleared

        """
        return await self._clear_impl(scope)

    async def _store_impl(
        self,
        key: str,
        content: dict[str, Any],
        scope: MemoryScope,
        metadata: dict[str, str] | None,
    ) -> MemoryEntry[dict[str, Any]]:
        """Store content in memory.

        Args:
        ----
            key: Key to store under
            content: Content to store
            scope: Storage scope
            metadata: Optional metadata

        Returns:
        -------
            Created memory entry

        Raises:
        ------
            RuntimeError: If storage fails

        """
        try:
            entry = MemoryEntry(
                key=key,
                value=content,
                scope=scope,
                metadata=metadata or {},
                type=MemoryType.SHORT_TERM,
                created_at=datetime.utcnow(),
                expires_at=None,
            )

            async with self._lock:
                self._entries[key] = entry

            return entry

        except Exception as e:
            logger.error(
                "Failed to store memory entry",
                extra={
                    "key": key,
                    "error": str(e),
                },
            )
            raise RuntimeError(f"Failed to store memory entry: {e}") from e

    def _is_expired(self, entry: MemoryEntry[dict[str, Any]], now: datetime) -> bool:
        """Check if an entry is expired.

        Args:
        ----
            entry: Entry to check
            now: Current time

        Returns:
        -------
            True if entry is expired

        """
        return bool(entry.expires_at and now > entry.expires_at)

    def _matches_filters(
        self,
        entry: MemoryEntry[dict[str, Any]],
        query: MemoryQuery,
    ) -> bool:
        """Check if entry matches query filters.

        Args:
        ----
            entry: Entry to check
            query: Query containing filters

        Returns:
        -------
            True if entry matches all filters

        """
        # Check filters
        if query.filters:
            if "scope" in query.filters and query.filters["scope"] != entry.scope:
                return False
            if "type" in query.filters and query.filters["type"] != entry.type:
                return False

        # Check metadata filter
        if query.metadata:
            if not entry.metadata:
                return False
            metadata = entry.metadata or {}
            if not all(metadata.get(k) == v for k, v in query.metadata.items()):
                return False

        return True

    def _matches_text_search(
        self,
        entry: MemoryEntry[dict[str, Any]],
        query_text: str | None,
    ) -> bool:
        """Check if entry matches text search.

        Args:
        ----
            entry: Entry to check
            query_text: Text to search for

        Returns:
        -------
            True if entry matches text search

        """
        if not query_text:
            return True

        content_str = str(entry.value)
        return query_text.lower() in content_str.lower()

    def _retrieve_impl(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemoryResult[dict[str, Any]]]:
        """Retrieve entries from memory.

        Args:
        ----
            query: Query parameters

        Returns:
        -------
            Iterator of memory results

        Raises:
        ------
            RuntimeError: If retrieval fails

        """

        async def _retrieve() -> AsyncIterator[MemoryResult[dict[str, Any]]]:
            try:
                count = 0
                now = datetime.utcnow()

                async with self._lock:
                    for key, entry in self._entries.items():
                        # Skip expired entries
                        if entry.expires_at and now > entry.expires_at:
                            continue

                        # Apply scope filter from query.filters
                        if (
                            "scope" in query.filters
                            and entry.scope != query.filters["scope"]
                        ):
                            continue

                        yield MemoryResult(
                            key=key,
                            entry=entry.value,
                            similarity=1.0,  # Basic search doesn't compute similarity
                            metadata=entry.metadata or {},
                        )

                        count += 1
                        if query.limit and count >= query.limit:
                            break

            except Exception as e:
                logger.error(
                    "Failed to retrieve memory entries",
                    extra={"query": str(query), "error": str(e)},
                )
                raise RuntimeError(f"Failed to retrieve memory entries: {e}") from e

        return _retrieve()

    async def _delete_impl(self, key: str) -> bool:
        """Delete an entry from memory.

        Args:
        ----
            key: Key to delete

        Returns:
        -------
            True if deleted, False if not found

        Raises:
        ------
            RuntimeError: If deletion fails

        """
        try:
            async with self._lock:
                if key not in self._entries:
                    return False

                del self._entries[key]
                return True

        except Exception as e:
            logger.error(
                "Failed to delete memory entry",
                extra={
                    "key": key,
                    "error": str(e),
                },
            )
            raise RuntimeError(f"Failed to delete memory entry: {e}") from e

    async def _exists_impl(self, key: str) -> bool:
        """Check if key exists in memory.

        Args:
        ----
            key: Key to check

        Returns:
        -------
            True if exists, False otherwise

        Raises:
        ------
            RuntimeError: If check fails

        """
        try:
            async with self._lock:
                return key in self._entries

        except Exception as e:
            logger.error(
                "Failed to check memory entry existence",
                extra={
                    "key": key,
                    "error": str(e),
                },
            )
            raise RuntimeError(f"Failed to check memory entry existence: {e}") from e

    async def _clear_impl(self, scope: MemoryScope | None = None) -> int:
        """Clear entries from memory.

        Args:
        ----
            scope: Optional scope to clear

        Returns:
        -------
            Number of entries cleared

        Raises:
        ------
            RuntimeError: If clearing fails

        """
        try:
            async with self._lock:
                if scope is None:
                    count = len(self._entries)
                    self._entries.clear()
                else:
                    keys_to_delete = [
                        key
                        for key, entry in self._entries.items()
                        if entry.scope == scope
                    ]
                    for key in keys_to_delete:
                        del self._entries[key]
                    count = len(keys_to_delete)

                return count

        except Exception as e:
            logger.error(
                "Failed to clear memory entries",
                extra={"scope": scope, "error": str(e)},
            )
            raise RuntimeError(f"Failed to clear memory entries: {e}") from e

    async def store(
        self,
        entry: MemoryEntry[Dict[str, Any]],
    ) -> MemoryEntry[Dict[str, Any]]:
        """Store a memory entry.

        Args:
            entry: Entry to store

        Returns:
            Stored entry

        Raises:
            MemoryError: If store operation fails
        """
        try:
            if not entry.key:
                raise MemoryKeyError("Entry key cannot be empty")

            self._entries[entry.key] = MemoryEntry(
                key=entry.key,
                value=entry.value,
                type=entry.type,
                scope=entry.scope,
                metadata=entry.metadata,
                created_at=entry.created_at,
                expires_at=entry.expires_at,
            )
            return entry
        except Exception as e:
            raise MemoryError(f"Failed to store entry: {e}") from e
