"""In-memory store implementation."""

import logging
from collections.abc import AsyncIterator
from typing import Any, Dict, TypeVar

from pepperpy.core.memory.base import (
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.core.memory.errors import MemoryKeyError
from pepperpy.core.memory.stores.base import BaseMemoryStore

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Dict[str, Any])


class InMemoryStore(BaseMemoryStore[T]):
    """Simple in-memory store implementation.

    This store keeps all entries in memory and provides basic search capabilities.
    It is suitable for testing and development, but not recommended for production use.
    """

    async def _store_entry(self, entry: MemoryEntry[T]) -> None:
        """Store a memory entry.

        Args:
            entry: Memory entry to store

        Raises:
            MemoryError: If storage fails

        """
        self._entries[entry.key] = entry

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
        try:
            return self._entries[key]
        except KeyError:
            raise MemoryKeyError(
                f"Memory key not found: {key}",
                details={"key": key},
            )

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
        for entry in self._entries.values():
            # Simple string matching for now
            if query.query.lower() in str(entry.value).lower():
                # Apply filters if any
                if all(
                    entry.value.get(k) == v
                    for k, v in query.filters.items()
                    if k in entry.value
                ):
                    # Apply metadata filters if any
                    if all(
                        entry.metadata.get(k) == v
                        for k, v in query.metadata.items()
                        if k in entry.metadata
                    ):
                        yield MemorySearchResult(
                            entry=entry,
                            score=1.0,  # Simple exact match score
                            metadata={},
                        )
