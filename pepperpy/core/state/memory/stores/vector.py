"""Vector store implementation for memory storage.

This module provides a vector-based storage backend for memory operations.
"""

from typing import Any, AsyncIterator, Dict, Optional

import numpy as np

from pepperpy.core.errors import PepperpyMemoryError
from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.memory.config import VectorStoreConfig
from pepperpy.memory.stores.types import VectorMemoryEntry
from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics import Counter, MetricsManager


class VectorStore(BaseMemoryStore[Dict[str, Any]]):
    """Vector-based memory storage.

    This class implements a vector store for memory entries, using
    vector similarity for retrieval.
    """

    def __init__(self, config: Optional[VectorStoreConfig] = None) -> None:
        """Initialize vector store.

        Args:
            config: Optional vector store configuration
        """
        super().__init__(name="vector")
        self.config = config or VectorStoreConfig()
        self._vectors: Dict[str, np.ndarray] = {}
        self._entries: Dict[str, VectorMemoryEntry] = {}
        self._metrics = MetricsManager.get_instance()
        self._counters: Dict[str, Counter] = {}

    async def _initialize(self) -> None:
        """Initialize the store and metrics."""
        # Initialize metrics
        self._counters["invalid_dimension"] = await self._metrics.create_counter(
            "memory.vector.invalid_dimension",
            "Number of invalid dimension errors",
        )
        self._counters["store_success"] = await self._metrics.create_counter(
            "memory.vector.successful_stores",
            "Number of successful store operations",
        )
        self._counters["store_error"] = await self._metrics.create_counter(
            "memory.vector.store_errors",
            "Number of store operation errors",
        )
        self._counters["retrieval_success"] = await self._metrics.create_counter(
            "memory.vector.successful_retrievals",
            "Number of successful retrieval operations",
        )
        self._counters["retrieval_error"] = await self._metrics.create_counter(
            "memory.vector.retrieval_errors",
            "Number of retrieval operation errors",
        )
        self._counters["not_found"] = await self._metrics.create_counter(
            "memory.vector.not_found",
            "Number of not found errors",
        )
        self._counters["deletion_success"] = await self._metrics.create_counter(
            "memory.vector.successful_deletions",
            "Number of successful deletion operations",
        )
        self._counters["deletion_error"] = await self._metrics.create_counter(
            "memory.vector.deletion_errors",
            "Number of deletion operation errors",
        )
        self._counters["exists_success"] = await self._metrics.create_counter(
            "memory.vector.successful_exists_checks",
            "Number of successful exists checks",
        )
        self._counters["exists_error"] = await self._metrics.create_counter(
            "memory.vector.exists_check_errors",
            "Number of exists check errors",
        )
        self._counters["cleanup_success"] = await self._metrics.create_counter(
            "memory.vector.successful_cleanups",
            "Number of successful cleanup operations",
        )
        self._counters["cleanup_error"] = await self._metrics.create_counter(
            "memory.vector.cleanup_errors",
            "Number of cleanup operation errors",
        )
        self._counters["search_success"] = await self._metrics.create_counter(
            "memory.vector.successful_searches",
            "Number of successful search operations",
        )
        self._counters["search_error"] = await self._metrics.create_counter(
            "memory.vector.search_errors",
            "Number of search operation errors",
        )

    async def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._vectors.clear()
            self._entries.clear()
            self._counters["cleanup_success"].record(1)
            logger.debug("Vector store cleaned up")
        except Exception as e:
            self._counters["cleanup_error"].record(1)
            raise PepperpyMemoryError(f"Failed to clean up vector store: {e}") from e

    async def _store(self, entry: MemoryEntry[Dict[str, Any]]) -> None:
        """Store a memory entry.

        Args:
            entry: Memory entry to store

        Raises:
            PepperpyMemoryError: If storage fails
        """
        try:
            if not isinstance(entry, VectorMemoryEntry):
                raise PepperpyMemoryError("Entry must be a VectorMemoryEntry")

            if not entry.embedding or len(entry.embedding) != self.config.dimension:
                self._counters["invalid_dimension"].record(1)
                raise PepperpyMemoryError(
                    f"Invalid embedding dimension: {len(entry.embedding) if entry.embedding else 0}, "
                    f"expected {self.config.dimension}"
                )

            entry_id = str(entry.id)
            self._vectors[entry_id] = np.array(entry.embedding)
            self._entries[entry_id] = entry
            self._counters["store_success"].record(1)
            logger.debug("Stored entry %s", entry_id)
        except Exception as e:
            self._counters["store_error"].record(1)
            raise PepperpyMemoryError(f"Failed to store entry: {e}") from e

    async def _retrieve(
        self, query: MemoryQuery
    ) -> AsyncIterator[MemorySearchResult[Dict[str, Any]]]:
        """Retrieve memory entries.

        Args:
            query: Memory query

        Yields:
            Memory search results

        Raises:
            PepperpyMemoryError: If retrieval fails
        """
        try:
            if query.key:
                if query.key not in self._entries:
                    self._counters["not_found"].record(1)
                    return

                entry = self._entries[query.key]
                yield MemorySearchResult(entry=entry, score=1.0)
                self._counters["retrieval_success"].record(1)
                return

            if query.keys:
                for key in query.keys:
                    if key in self._entries:
                        entry = self._entries[key]
                        yield MemorySearchResult(entry=entry, score=1.0)
                self._counters["retrieval_success"].record(1)
                return

            # TODO: Implement semantic search
            self._counters["retrieval_success"].record(1)

        except Exception as e:
            self._counters["retrieval_error"].record(1)
            raise PepperpyMemoryError(f"Failed to retrieve entries: {e}") from e

    async def _delete(self, key: str) -> None:
        """Delete a memory entry.

        Args:
            key: Entry key

        Raises:
            PepperpyMemoryError: If deletion fails
        """
        try:
            if key not in self._entries:
                self._counters["not_found"].record(1)
                raise PepperpyMemoryError(f"Entry not found: {key}")

            del self._vectors[key]
            del self._entries[key]
            self._counters["deletion_success"].record(1)
            logger.debug("Deleted entry %s", key)
        except Exception as e:
            self._counters["deletion_error"].record(1)
            raise PepperpyMemoryError(f"Failed to delete entry: {e}") from e

    async def clear(self) -> None:
        """Clear all data from memory."""
        try:
            self._vectors.clear()
            self._entries.clear()
            self._counters["cleanup_success"].record(1)
            logger.debug("Vector store cleared")
        except Exception as e:
            self._counters["cleanup_error"].record(1)
            raise PepperpyMemoryError(f"Failed to clear vector store: {e}") from e

    async def search(
        self, query: MemoryQuery
    ) -> AsyncIterator[MemorySearchResult[Dict[str, Any]]]:
        """Search memory entries.

        Args:
            query: Search parameters

        Yields:
            Search results ordered by relevance

        Raises:
            ValueError: If query is invalid
            PepperpyMemoryError: If search fails
        """
        try:
            # For now, just use the retrieve method
            # TODO: Implement semantic search
            async for result in self._retrieve(query):
                yield result
            self._counters["search_success"].record(1)
        except Exception as e:
            self._counters["search_error"].record(1)
            raise PepperpyMemoryError(f"Failed to search entries: {e}") from e
