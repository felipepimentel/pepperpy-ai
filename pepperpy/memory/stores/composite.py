"""Composite memory store implementation."""

from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.memory.errors import MemoryError


class CompositeMemoryStore(BaseMemoryStore[Dict[str, Any]]):
    """Composite memory store implementation.

    This store combines multiple memory stores into a single interface.
    Operations are performed on all stores in sequence.
    """

    def __init__(
        self,
        name: str,
        stores: Optional[List[BaseMemoryStore[Dict[str, Any]]]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize composite store.

        Args:
            name: Store name
            stores: List of memory stores
            config: Store configuration

        """
        super().__init__(name=name)
        self._stores = stores or []
        self._config = config or {}

    async def _initialize(self) -> None:
        """Initialize all stores."""
        for store in self._stores:
            await store.initialize()

    async def _cleanup(self) -> None:
        """Clean up all stores."""
        for store in self._stores:
            await store.cleanup()

    async def _store(self, entry: MemoryEntry[Dict[str, Any]]) -> None:
        """Store entry in all stores.

        Args:
            entry: Memory entry to store

        Raises:
            MemoryError: If storing fails in any store

        """
        errors = []
        for store in self._stores:
            try:
                await store.store(entry)
            except Exception as e:
                errors.append(f"{store.name}: {e}")

        if errors:
            raise MemoryError(f"Failed to store in some stores: {', '.join(errors)}")

    async def _retrieve(
        self, query: MemoryQuery
    ) -> AsyncIterator[MemorySearchResult[Dict[str, Any]]]:
        """Retrieve from all stores.

        Args:
            query: Memory query

        Yields:
            Memory search results from all stores

        """
        seen_keys = set()
        for store in self._stores:
            async for result in store.retrieve(query):
                if result.entry.key not in seen_keys:
                    seen_keys.add(result.entry.key)
                    yield result

    async def _delete(self, key: str) -> None:
        """Delete from all stores.

        Args:
            key: Key to delete

        Raises:
            MemoryError: If deletion fails in any store

        """
        errors = []
        for store in self._stores:
            try:
                await store.delete(key)
            except Exception as e:
                errors.append(f"{store.name}: {e}")

        if errors:
            raise MemoryError(f"Failed to delete from some stores: {', '.join(errors)}")

    async def add_store(self, store: BaseMemoryStore[Dict[str, Any]]) -> None:
        """Add a store to the composite.

        Args:
            store: Store to add

        """
        if not store.is_initialized:
            await store.initialize()
        self._stores.append(store)

    async def remove_store(self, store: BaseMemoryStore[Dict[str, Any]]) -> None:
        """Remove a store from the composite.

        Args:
            store: Store to remove

        """
        if store in self._stores:
            await store.cleanup()
            self._stores.remove(store)
