"""Composite memory store implementation."""

import logging
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.memory.base import (
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.core.memory.errors import (
    MemoryKeyError,
    MemoryQueryError,
    MemoryStorageError,
)
from pepperpy.core.memory.stores.base import BaseMemoryStore

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Dict[str, Any])


class CompositeMemoryStore(BaseMemoryStore[T]):
    """Composite memory store that combines multiple stores.

    This store allows combining multiple memory stores with different characteristics
    (e.g., in-memory, persistent, distributed) into a single unified interface.
    """

    def __init__(self, stores: Optional[List[BaseMemoryStore[T]]] = None) -> None:
        """Initialize the composite memory store.

        Args:
            stores: Optional list of memory stores

        """
        super().__init__()
        self._stores = stores or []

    async def _store_entry(self, entry: MemoryEntry[T]) -> None:
        """Store a memory entry in all stores.

        Args:
            entry: Memory entry to store

        Raises:
            MemoryStorageError: If storage fails in any store

        """
        errors = []
        for store in self._stores:
            try:
                await store._store_entry(entry)
            except Exception as e:
                errors.append({
                    "store": store.__class__.__name__,
                    "error": str(e),
                })

        if errors:
            raise MemoryStorageError(
                "Failed to store memory entry in one or more stores",
                details={"errors": errors},
            )

    async def _retrieve_entry(self, key: str) -> MemoryEntry[T]:
        """Retrieve a memory entry from the first store that has it.

        Args:
            key: Memory key

        Returns:
            Memory entry

        Raises:
            KeyError: If key not found in any store
            MemoryStorageError: If retrieval fails in all stores

        """
        errors = []
        for store in self._stores:
            try:
                return await store._retrieve_entry(key)
            except KeyError:
                continue
            except Exception as e:
                errors.append({
                    "store": store.__class__.__name__,
                    "error": str(e),
                })

        if errors:
            raise MemoryStorageError(
                "Failed to retrieve memory entry from all stores",
                details={"errors": errors},
            )
        raise MemoryKeyError(
            f"Memory key not found in any store: {key}",
            details={"key": key},
        )

    async def _search_entries(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Search memory entries across all stores.

        Args:
            query: Search parameters

        Yields:
            Search results ordered by relevance

        Raises:
            MemoryQueryError: If search fails in all stores

        """
        errors = []
        for store in self._stores:
            try:
                results = await store._search_entries(query)
                async for result in results:
                    yield result
            except Exception as e:
                errors.append({
                    "store": store.__class__.__name__,
                    "error": str(e),
                })

        if errors and len(errors) == len(self._stores):
            raise MemoryQueryError(
                "Failed to search memory entries in all stores",
                details={"errors": errors},
            )
