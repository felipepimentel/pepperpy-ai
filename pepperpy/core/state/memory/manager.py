"""Memory system manager.

This module provides the memory manager that coordinates between different
memory types and handles the lifecycle of memory entries.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Any, Generic, TypeVar
from uuid import UUID

from pepperpy.core.errors import ConfigurationError

from .base import (
    BaseMemory,
    MemoryEntry,
    MemoryQuery,
    MemoryScope,
    MemorySearchResult,
    MemoryType,
)

logger = logging.getLogger(__name__)

K = TypeVar("K", str, UUID)


class MemoryManager(Generic[K]):
    """Memory manager implementation.

    This class manages different types of memory storage (short-term,
    medium-term, and long-term) and provides a unified interface for
    storing and retrieving memory entries.

    Type Parameters:
        K: Key type
    """

    def __init__(
        self,
        short_term: BaseMemory[K, dict[str, Any]],
        medium_term: BaseMemory[K, dict[str, Any]] | None = None,
        long_term: BaseMemory[K, dict[str, Any]] | None = None,
        cleanup_interval: int = 300,  # 5 minutes
        reindex_interval: int = 3600,  # 1 hour
    ) -> None:
        """Initialize memory manager.

        Args:
            short_term: Short-term memory store
            medium_term: Medium-term memory store
            long_term: Long-term memory store
            cleanup_interval: Interval in seconds for cleaning up expired entries
            reindex_interval: Interval in seconds for reindexing entries
        """
        self._memories: dict[MemoryType, BaseMemory[K, dict[str, Any]]] = {
            MemoryType.SHORT_TERM: short_term,
        }
        if medium_term:
            self._memories[MemoryType.MEDIUM_TERM] = medium_term
        if long_term:
            self._memories[MemoryType.LONG_TERM] = long_term

        self._cleanup_interval = cleanup_interval
        self._reindex_interval = reindex_interval
        self._cleanup_task: asyncio.Task[None] | None = None
        self._reindex_task: asyncio.Task[None] | None = None
        self._active = False

    @property
    def is_active(self) -> bool:
        """Check if manager is active."""
        return self._active

    async def start(self) -> None:
        """Start the memory manager.

        This starts the background cleanup task.

        Raises:
            ConfigurationError: If no memory implementations are configured
            RuntimeError: If manager is already active
        """
        if self._active:
            raise RuntimeError("Memory manager is already active")

        if not self._memories:
            raise ConfigurationError("No memory implementations configured")

        self._active = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop the memory manager.

        This stops the background cleanup task and cleans up resources.
        """
        self._active = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up expired entries."""
        while self._active:
            try:
                total_cleaned = 0
                for memory in self._memories.values():
                    cleaned = await memory.cleanup_expired()
                    total_cleaned += cleaned

                if total_cleaned > 0:
                    logger.info(
                        "Cleaned up expired memory entries",
                        extra={"count": total_cleaned},
                    )

            except Exception as e:
                logger.error(
                    "Error cleaning up expired memory entries",
                    extra={"error": str(e)},
                )

            await asyncio.sleep(self._cleanup_interval)

    def _get_memory(self, type: MemoryType) -> BaseMemory[K, dict[str, Any]]:
        """Get memory implementation for type.

        Args:
            type: Memory type to get

        Returns:
            Memory implementation

        Raises:
            ConfigurationError: If memory type is not configured
        """
        memory = self._memories.get(type)
        if not memory:
            raise ConfigurationError(f"Memory type not configured: {type}")
        return memory

    async def store(
        self,
        key: K,
        value: dict[str, Any],
        type: MemoryType = MemoryType.SHORT_TERM,
        scope: MemoryScope = MemoryScope.SESSION,
        metadata: dict[str, Any] | None = None,
        expires_in: timedelta | None = None,
    ) -> MemoryEntry[dict[str, Any]]:
        """Store data in memory.

        Args:
            key: Memory key
            value: Value to store
            type: Memory type
            scope: Storage scope
            metadata: Optional metadata
            expires_in: Optional expiration time

        Returns:
            Created memory entry

        Raises:
            MemoryError: If storing fails
            ValueError: If memory type is invalid
        """
        memory = self._get_memory(type)
        return await memory.store(
            key,
            value,
            type=type,
            scope=scope,
            metadata=metadata,
            expires_at=datetime.utcnow() + expires_in if expires_in else None,
        )

    async def retrieve(
        self,
        key: K,
        type: MemoryType | None = None,
    ) -> MemoryEntry[dict[str, Any]]:
        """Retrieve data from memory.

        Args:
            key: Memory key
            type: Optional memory type

        Returns:
            Memory entry

        Raises:
            MemoryError: If retrieval fails
            KeyError: If key not found
            ValueError: If memory type is invalid
        """
        if type:
            memory = self._get_memory(type)
            return await memory.retrieve(key, type=type)

        # Try all memory types in order
        for memory_type in MemoryType:
            try:
                memory = self._get_memory(memory_type)
                return await memory.retrieve(key, type=memory_type)
            except KeyError:
                continue

        raise KeyError(f"Memory key not found: {key}")

    async def search(
        self,
        query: MemoryQuery,
        type: MemoryType | None = None,
    ) -> AsyncIterator[MemorySearchResult[dict[str, Any]]]:
        """Search memory entries.

        Args:
            query: Query parameters
            type: Optional memory type

        Yields:
            Memory entries matching the query

        Raises:
            MemoryError: If search fails
            ValueError: If memory type is invalid
        """
        if type:
            memory = self._get_memory(type)
            async for result in await memory.search(query):
                yield result
            return

        # Search all memory types
        for memory_type in MemoryType:
            try:
                memory = self._get_memory(memory_type)
                async for result in await memory.search(query):
                    yield result
            except Exception as e:
                logger.warning(f"Failed to search memory type {memory_type}: {e}")
                continue

    async def similar(
        self,
        key: K,
        type: MemoryType | None = None,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> AsyncIterator[MemorySearchResult[dict[str, Any]]]:
        """Find similar entries.

        Args:
            key: Memory key
            type: Optional memory type
            limit: Maximum number of results
            min_score: Minimum similarity score

        Yields:
            Similar memory entries

        Raises:
            MemoryError: If similarity search fails
            KeyError: If key not found
            ValueError: If memory type is invalid
        """
        if type:
            memory = self._get_memory(type)
            async for result in await memory.similar(
                key, limit=limit, min_score=min_score
            ):
                yield result
            return

        # Search all memory types
        for memory_type in MemoryType:
            try:
                memory = self._get_memory(memory_type)
                async for result in await memory.similar(
                    key, limit=limit, min_score=min_score
                ):
                    yield result
            except Exception as e:
                logger.warning(
                    f"Failed to find similar entries in memory type {memory_type}: {e}"
                )
                continue
