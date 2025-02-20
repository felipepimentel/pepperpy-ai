"""Vector store implementation for memory storage.

This module provides a vector-based storage backend for memory operations.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel

from pepperpy.core.errors import PepperpyMemoryError
from pepperpy.memory.base import MemoryBackend
from pepperpy.memory.stores.types import VectorMemoryEntry
from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics import Counter, MetricsManager


class VectorConfig(BaseModel):
    """Configuration for vector store."""

    dimension: int = 1536  # Default for OpenAI embeddings
    similarity_threshold: float = 0.8
    max_results: int = 10
    storage_path: Optional[Path] = None


class VectorStore(MemoryBackend):
    """Vector-based memory storage.

    This class implements a vector store for memory entries, using
    vector similarity for retrieval.
    """

    def __init__(self, config: Optional[VectorConfig] = None) -> None:
        """Initialize vector store.

        Args:
            config: Optional vector store configuration
        """
        self.config = config or VectorConfig()
        self._vectors: Dict[str, np.ndarray] = {}
        self._entries: Dict[str, VectorMemoryEntry] = {}
        self._metrics = MetricsManager.get_instance()
        self._counters: Dict[str, Counter] = {}

    async def initialize(self) -> None:
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

    async def store(self, entry: VectorMemoryEntry) -> None:
        """Store a memory entry.

        Args:
            entry: Memory entry to store

        Raises:
            PepperpyMemoryError: If storage fails
        """
        try:
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

    async def retrieve(
        self, query_embedding: List[float], limit: Optional[int] = None
    ) -> List[Tuple[VectorMemoryEntry, float]]:
        """Retrieve similar entries.

        Args:
            query_embedding: Query vector
            limit: Maximum number of results

        Returns:
            List of (entry, similarity) tuples

        Raises:
            PepperpyMemoryError: If retrieval fails
        """
        try:
            if len(query_embedding) != self.config.dimension:
                self._counters["invalid_dimension"].record(1)
                raise PepperpyMemoryError(
                    f"Invalid query dimension: {len(query_embedding)}, "
                    f"expected {self.config.dimension}"
                )

            query_vector = np.array(query_embedding)
            results = []

            for entry_id, vector in self._vectors.items():
                similarity = np.dot(query_vector, vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(vector)
                )
                if similarity >= self.config.similarity_threshold:
                    results.append((self._entries[entry_id], float(similarity)))

            results.sort(key=lambda x: x[1], reverse=True)
            limit = limit or self.config.max_results
            self._counters["retrieval_success"].record(1)
            return results[:limit]
        except Exception as e:
            self._counters["retrieval_error"].record(1)
            raise PepperpyMemoryError(f"Failed to retrieve entries: {e}") from e

    async def delete(self, entry_id: str) -> None:
        """Delete a memory entry.

        Args:
            entry_id: ID of entry to delete

        Raises:
            PepperpyMemoryError: If deletion fails
        """
        try:
            if entry_id not in self._entries:
                self._counters["not_found"].record(1)
                raise PepperpyMemoryError(f"Entry not found: {entry_id}")

            del self._vectors[entry_id]
            del self._entries[entry_id]
            self._counters["deletion_success"].record(1)
            logger.debug("Deleted entry %s", entry_id)
        except Exception as e:
            self._counters["deletion_error"].record(1)
            raise PepperpyMemoryError(f"Failed to delete entry: {e}") from e

    async def exists(self, entry_id: str) -> bool:
        """Check if entry exists.

        Args:
            entry_id: ID to check

        Returns:
            True if entry exists, False otherwise

        Raises:
            PepperpyMemoryError: If check fails
        """
        try:
            exists = entry_id in self._entries
            self._counters["exists_success"].record(1)
            return exists
        except Exception as e:
            self._counters["exists_error"].record(1)
            raise PepperpyMemoryError(f"Failed to check entry existence: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._vectors.clear()
            self._entries.clear()
            self._counters["cleanup_success"].record(1)
            logger.debug("Vector store cleaned up")
        except Exception as e:
            self._counters["cleanup_error"].record(1)
            raise PepperpyMemoryError(f"Failed to clean up vector store: {e}") from e
