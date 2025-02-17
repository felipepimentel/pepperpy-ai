"""Composite memory store implementation."""

import asyncio
import logging
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, TypeVar

from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.memory.config import MemoryConfig

logger = logging.getLogger(__name__)

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
        config: MemoryConfig,
        primary_store: BaseMemoryStore[T],
    ) -> None:
        """Initialize composite store.

        Args:
            config: Store configuration
            primary_store: Primary store for persistence

        """
        super().__init__(name="composite")
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
            RuntimeError: If storage fails

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
                            store_type=store.__class__.__name__,
                            error=str(e),
                        )
            except Exception as e:
                raise RuntimeError(f"Failed to store in primary store: {e}") from e

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
                store_type=self._primary_store.__class__.__name__,
                error=str(e),
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
                        store_type=store.__class__.__name__,
                        error=str(e),
                    )
                    continue  # Continue with other stores on error

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
                            store_type=store.__class__.__name__,
                            error=str(e),
                        )
            except Exception as e:
                logger.error(
                    "Failed to delete from primary store",
                    store_type=self.__class__.__name__,
                    error=str(e),
                )
                raise RuntimeError("Failed to delete from primary store") from e

    async def add_store(self, store: BaseMemoryStore[T]) -> None:
        """Add a store to the composite.

        Args:
            store: Store to add

        """
        async with self._lock:
            if store not in self._stores:
                self._stores.append(store)
                logger.debug(
                    "Added store to composite",
                    store_type=store.__class__.__name__,
                    total_stores=str(len(self._stores)),
                )

    async def retrieve(
        self,
        query: MemoryQuery,
    ) -> AsyncGenerator[MemorySearchResult[T], None]:
        """Retrieve entries from memory.

        Args:
            query: Query parameters

        Returns:
            Generator of memory results

        Raises:
            ValueError: If query is invalid
            RuntimeError: If retrieval fails

        """
        if not query:
            raise ValueError("Query cannot be empty")

        async for result in self._retrieve(query):
            yield result

    async def search(self, query: MemoryQuery) -> AsyncIterator[MemorySearchResult[T]]:
        """Search memory entries.

        Args:
            query: Search parameters

        Yields:
            Search results ordered by relevance

        Raises:
            ValueError: If query is invalid
            MemoryError: If search fails

        """
        async for result in self._retrieve(query):
            yield result

    async def similar(
        self,
        key: str,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Find similar entries.

        Args:
            key: Memory key to find similar entries for
            limit: Maximum number of results
            min_score: Minimum similarity score

        Yields:
            Similar entries ordered by similarity

        Raises:
            KeyError: If key not found
            ValueError: If parameters are invalid
            MemoryError: If similarity search fails

        """
        # For now, just return entries with the same key
        query = MemoryQuery(
            query="",
            key=key,
            limit=limit,
            min_score=min_score,
        )
        async for result in self._retrieve(query):
            yield result
