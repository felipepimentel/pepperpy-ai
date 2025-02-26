"""Composite memory store implementation."""

from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

from pepperpy.core.logging import get_logger
from pepperpy.memory.store import BaseMemoryStore
from pepperpy.memory.types import (
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryScope,
)

# Configure logger
logger = get_logger(__name__)


class CompositeMemoryStore(BaseMemoryStore[Dict[str, Any]]):
    """Composite memory store implementation.

    This store combines multiple memory stores into a single interface.
    Operations are performed on all stores in sequence.
    """

    def __init__(
        self,
        stores: Optional[List[BaseMemoryStore[Dict[str, Any]]]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize composite store.

        Args:
            stores: List of memory stores
            config: Store configuration
        """
        self._stores = stores or []
        self._config = config or {}

    async def _store_impl(
        self,
        key: str,
        content: Dict[str, Any],
        scope: MemoryScope,
        metadata: Dict[str, str] | None,
    ) -> MemoryEntry[Dict[str, Any]]:
        """Store content in memory.

        Args:
            key: Key to store under
            content: Content to store
            scope: Storage scope
            metadata: Optional metadata

        Returns:
            Created memory entry

        Raises:
            RuntimeError: If storage fails
        """
        errors = []
        entry = None

        for store in self._stores:
            try:
                entry = await store.store(key, content, scope, metadata)
            except Exception as e:
                errors.append(str(e))

        if errors:
            raise RuntimeError(f"Failed to store in some stores: {', '.join(errors)}")

        if not entry:
            raise RuntimeError("No stores available to store content")

        return entry

    def _retrieve_impl(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemoryResult[Dict[str, Any]]]:
        """Retrieve entries from memory.

        Args:
            query: Query parameters

        Returns:
            Iterator of memory results

        Raises:
            RuntimeError: If retrieval fails
        """

        async def _retrieve() -> AsyncIterator[MemoryResult[Dict[str, Any]]]:
            seen_keys = set()
            for store in self._stores:
                try:
                    async for result in store.retrieve(query):
                        if result.key not in seen_keys:
                            seen_keys.add(result.key)
                            yield result
                except Exception as e:
                    logger.error(
                        "Failed to retrieve from store",
                        extra={"error": str(e)},
                    )

        return _retrieve()

    async def _delete_impl(self, key: str) -> bool:
        """Delete an entry from memory.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found

        Raises:
            RuntimeError: If deletion fails
        """
        errors = []
        deleted = False

        for store in self._stores:
            try:
                if await store.delete(key):
                    deleted = True
            except Exception as e:
                errors.append(str(e))

        if errors:
            raise RuntimeError(
                f"Failed to delete from some stores: {', '.join(errors)}"
            )

        return deleted

    async def _exists_impl(self, key: str) -> bool:
        """Check if key exists in memory.

        Args:
            key: Key to check

        Returns:
            True if exists, False otherwise

        Raises:
            RuntimeError: If check fails
        """
        for store in self._stores:
            try:
                if await store.exists(key):
                    return True
            except Exception as e:
                logger.error(
                    "Failed to check existence in store",
                    extra={"error": str(e)},
                )
        return False

    async def _clear_impl(self, scope: MemoryScope | None = None) -> int:
        """Clear entries from memory.

        Args:
            scope: Optional scope to clear

        Returns:
            Number of entries cleared

        Raises:
            RuntimeError: If clearing fails
        """
        errors = []
        total_cleared = 0

        for store in self._stores:
            try:
                cleared = await store.clear(scope)
                total_cleared += cleared
            except Exception as e:
                errors.append(str(e))

        if errors:
            raise RuntimeError(f"Failed to clear some stores: {', '.join(errors)}")

        return total_cleared

    async def add_store(self, store: BaseMemoryStore[Dict[str, Any]]) -> None:
        """Add a store to the composite.

        Args:
            store: Store to add
        """
        self._stores.append(store)

    async def remove_store(self, store: BaseMemoryStore[Dict[str, Any]]) -> None:
        """Remove a store from the composite.

        Args:
            store: Store to remove
        """
        if store in self._stores:
            self._stores.remove(store)
