"""Base memory store implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, Dict, Optional, TypeVar

from pepperpy.core.logging import get_logger
from pepperpy.core.memory.base import (
    BaseMemory,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
    MemoryType,
)
from pepperpy.core.memory.errors import (
    MemoryKeyError,
    MemoryQueryError,
    MemoryStorageError,
    MemoryTypeError,
)

# Configure logging
logger = get_logger(__name__)

T = TypeVar("T", bound=Dict[str, Any])


class BaseMemoryStore(BaseMemory[T], ABC):
    """Base class for memory store implementations."""

    def __init__(self) -> None:
        """Initialize the memory store."""
        self._entries: Dict[str, MemoryEntry[T]] = {}

    async def store(
        self,
        key: str,
        value: T,
        type: MemoryType = MemoryType.SHORT_TERM,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> MemoryEntry[T]:
        """Store data in memory.

        Args:
            key: Memory key
            value: Value to store
            type: Type of memory storage
            metadata: Optional metadata
            expires_at: Optional expiration time

        Returns:
            Created memory entry

        Raises:
            ValueError: If key is invalid
            TypeError: If value type is not supported
            MemoryError: If storage fails

        """
        if not key:
            raise MemoryKeyError("Memory key cannot be empty")

        if not isinstance(value, dict):
            raise MemoryTypeError("Memory value must be a dictionary")

        try:
            entry = MemoryEntry(
                key=key,
                value=value,
                type=type,
                created_at=datetime.now(UTC),
                expires_at=expires_at,
                metadata=metadata or {},
            )
            await self._store_entry(entry)
            return entry
        except Exception as e:
            raise MemoryStorageError(
                f"Failed to store memory entry: {e}",
                details={"key": key, "type": type},
            ) from e

    @abstractmethod
    async def _store_entry(self, entry: MemoryEntry[T]) -> None:
        """Store a memory entry.

        Args:
            entry: Memory entry to store

        Raises:
            MemoryError: If storage fails

        """
        pass

    async def retrieve(
        self,
        key: str,
        type: Optional[MemoryType] = None,
    ) -> MemoryEntry[T]:
        """Retrieve data from memory.

        Args:
            key: Memory key
            type: Optional memory type filter

        Returns:
            Memory entry

        Raises:
            KeyError: If key not found
            ValueError: If key is invalid
            MemoryError: If retrieval fails

        """
        if not key:
            raise MemoryKeyError("Memory key cannot be empty")

        try:
            entry = await self._retrieve_entry(key)
            if type and entry.type != type:
                raise MemoryTypeError(
                    f"Memory entry type mismatch: expected {type}, got {entry.type}",
                    details={
                        "key": key,
                        "expected_type": type,
                        "actual_type": entry.type,
                    },
                )
            return entry
        except KeyError:
            raise MemoryKeyError(
                f"Memory key not found: {key}",
                details={"key": key, "type": type},
            )
        except Exception as e:
            raise MemoryStorageError(
                f"Failed to retrieve memory entry: {e}",
                details={"key": key, "type": type},
            ) from e

    @abstractmethod
    async def _retrieve_entry(self, key: str) -> MemoryEntry[T]:
        """Retrieve a memory entry.

        Args:
            key: Memory key

        Returns:
            Memory entry

        Raises:
            KeyError: If key not found
            MemoryError: If retrieval fails

        """
        pass

    async def search(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Search memory entries.

        Args:
            query: Search parameters

        Yields:
            Search results ordered by relevance

        Raises:
            ValueError: If query is invalid
            MemoryError: If search fails

        """
        if not query.query:
            raise MemoryQueryError("Search query cannot be empty")

        try:
            results = await self._search_entries(query)
            async for result in results:
                yield result
        except Exception as e:
            raise MemoryQueryError(
                f"Failed to search memory entries: {e}",
                details={"query": query.model_dump()},
            ) from e

    @abstractmethod
    async def _search_entries(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Search memory entries.

        Args:
            query: Search parameters

        Yields:
            Search results ordered by relevance

        Raises:
            MemoryError: If search fails

        """
        pass
