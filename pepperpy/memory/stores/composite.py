"""Composite memory store implementation."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any, TypeVar

from pepperpy.common.errors import MemoryError
from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.memory.store_config import CompositeConfig
from pepperpy.monitoring import logger

T = TypeVar("T", bound=dict[str, Any])


class CompositeMemoryStore(BaseMemoryStore[T]):
    """Composite memory store that combines multiple stores.

    This store allows combining multiple memory stores to provide:
    - Fast access through caching
    - Vector search capabilities
    - Persistent storage
    """

    def __init__(
        self,
        config: CompositeConfig,
        primary_store: BaseMemoryStore[T],
    ) -> None:
        """Initialize composite store.

        Args:
            config: Store configuration
            primary_store: Primary store for persistence
        """
        super().__init__("composite")
        self._config = config
        self._primary_store = primary_store
        self._stores: list[BaseMemoryStore[T]] = [primary_store]
        self._lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """Initialize all stores."""
        for store in self._stores:
            await store.initialize()

    async def _cleanup(self) -> None:
        """Clean up all stores."""
        for store in self._stores:
            await store.cleanup()

    async def _store(self, entry: MemoryEntry[T]) -> None:
        """Store entry in all stores.

        Args:
            entry: Entry to store

        Raises:
            MemoryError: If storage fails
        """
        async with self._lock:
            try:
                # Store in primary first
                await self._primary_store.store(entry)

                # Then store in secondary stores
                for store in self._stores[1:]:
                    try:
                        await store.store(entry)
                    except Exception as e:
                        logger.error(
                            "Failed to store in secondary store",
                            store=str(store),
                            error=str(e),
                        )
            except Exception as e:
                raise MemoryError(f"Failed to store in primary store: {e}") from e

    async def _retrieve(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Retrieve memories from all stores.

        Args:
            query: Memory query parameters.

        Yields:
            Memory search results from all stores.

        Raises:
            MemoryError: If retrieval from all stores fails.
        """
        # Get results from primary store first
        try:
            async for result in self._primary_store._retrieve(query):
                yield result
        except Exception as e:
            logger.error(
                "Failed to retrieve from primary store",
                extra={
                    "error": str(e),
                    "store": self._primary_store.__class__.__name__,
                },
            )

        # Then get results from additional stores
        for store in self._stores:
            if (
                store is not self._primary_store
            ):  # Skip primary store since we already processed it
                try:
                    async for result in store._retrieve(query):
                        yield result
                except Exception as e:
                    logger.error(
                        "Failed to retrieve from store",
                        extra={"error": str(e), "store": store.__class__.__name__},
                    )
                    continue  # Continue with other stores on error

    async def _retrieve_from_store(
        self,
        store: BaseMemoryStore[T],
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Retrieve memories from a single store.

        Args:
            store: Memory store to retrieve from.
            query: Memory query parameters.

        Returns:
            Memory search results from the store.
        """
        try:
            async for result in store._retrieve(query):
                yield result
        except Exception as e:
            logger.error(
                "Failed to retrieve from store",
                extra={"error": str(e), "store": store.__class__.__name__},
            )
            # Continue with other stores on error

    async def _delete(self, key: str) -> None:
        """Delete an entry from memory.

        Args:
            key: Key to delete

        Raises:
            MemoryError: If deletion fails
        """
        async with self._lock:
            try:
                # Delete from primary first
                await self._primary_store.delete(key)

                # Then delete from secondary stores
                for store in self._stores[1:]:
                    try:
                        await store.delete(key)
                    except Exception as e:
                        logger.error(
                            "Failed to delete from secondary store",
                            store=str(store),
                            error=str(e),
                        )
            except Exception as e:
                raise MemoryError(f"Failed to delete from primary store: {e}") from e

    async def add_store(self, store: BaseMemoryStore[T]) -> None:
        """Add a store to the composite.

        Args:
            store: Memory store to add
        """
        async with self._lock:
            if store not in self._stores:
                self._stores.append(store)
                logger.debug(
                    "Added store to composite",
                    store=str(store),
                    total_stores=len(self._stores),
                )
