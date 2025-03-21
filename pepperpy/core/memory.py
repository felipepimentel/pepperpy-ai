"""Memory management module for PepperPy.

This module provides memory management capabilities for storing and retrieving
data with metadata and timestamps.

Example:
    >>> from pepperpy.core.memory import BaseMemory, MemoryManager
    >>> memory = BaseMemory(content="Hello", metadata={"type": "greeting"})
    >>> async with MemoryManager() as manager:
    ...     await manager.store(memory)
    ...     memories = await manager.get_by_filter(lambda x: x.metadata["type"] == "greeting")
"""

import abc
import asyncio
from datetime import datetime
from typing import Any, Callable, List, Optional, TypeVar

from pepperpy.core.types import Metadata

T = TypeVar("T", bound="BaseMemory")


class BaseMemory(abc.ABC):
    """Base class for memory items."""

    def __init__(self, metadata: Optional[Metadata] = None) -> None:
        """Initialize memory item.

        Args:
            metadata: Optional metadata dictionary
        """
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.last_accessed = self.created_at
        self.access_count = 0

    def update_access(self) -> None:
        """Update memory access statistics."""
        self.last_accessed = datetime.now()
        self.access_count += 1


class MemoryManager:
    """Manager for storing and retrieving memories."""

    def __init__(self) -> None:
        """Initialize memory manager."""
        self._memories: List[BaseMemory] = []
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "MemoryManager":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.cleanup()

    async def store(self, memory: BaseMemory) -> None:
        """Store a memory item.

        Args:
            memory: Memory item to store
        """
        async with self._lock:
            self._memories.append(memory)

    async def get_by_filter(
        self,
        filter_fn: Callable[[BaseMemory], bool],
    ) -> List[BaseMemory]:
        """Get memories matching a filter.

        Args:
            filter_fn: Filter function to apply

        Returns:
            List of matching memories
        """
        async with self._lock:
            matches = [m for m in self._memories if filter_fn(m)]
            for memory in matches:
                memory.update_access()
            return matches

    async def cleanup(self) -> None:
        """Clean up memory resources."""
        async with self._lock:
            self._memories.clear()
