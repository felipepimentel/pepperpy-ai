"""Memory management for PepperPy.

This module provides memory management functionality for storing and retrieving
data during framework operations.

Example:
    >>> from pepperpy.core.memory import BaseMemory, MemoryManager
    >>> memory = BaseMemory(content="Hello", metadata={"type": "greeting"})
    >>> async with MemoryManager() as manager:
    ...     await manager.store(memory)
    ...     memories = await manager.get_by_filter(lambda x: x.metadata["type"] == "greeting")
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from pepperpy.core.base import Metadata


class BaseMemory(ABC):
    """Base class for memory implementations."""

    def __init__(self, name: str = "base", **kwargs: Any) -> None:
        """Initialize memory.

        Args:
            name: Memory name
            **kwargs: Additional memory-specific configuration
        """
        self.name = name
        self._data: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}

    @property
    def data(self) -> Dict[str, Any]:
        """Get stored data.

        Returns:
            Dictionary of stored data
        """
        return self._data

    @property
    def metadata(self) -> Metadata:
        """Get memory metadata.

        Returns:
            Dictionary of metadata
        """
        return self._metadata

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from memory.

        Args:
            key: Key to get
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in memory.

        Args:
            key: Key to set
            value: Value to store
        """
        self._data[key] = value

    def delete(self, key: str) -> None:
        """Delete a value from memory.

        Args:
            key: Key to delete
        """
        self._data.pop(key, None)

    def clear(self) -> None:
        """Clear all stored data."""
        self._data.clear()
        self._metadata.clear()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value.

        Args:
            key: Key to get
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value.

        Args:
            key: Key to set
            value: Value to store
        """
        self._metadata[key] = value

    @abstractmethod
    def load(self, path: str) -> None:
        """Load memory from storage.

        Args:
            path: Path to load from
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Save memory to storage.

        Args:
            path: Path to save to
        """
        pass


class MemoryManager:
    """Manager for memory instances."""

    def __init__(self) -> None:
        """Initialize memory manager."""
        self._memories: List[BaseMemory] = []

    def add(self, memory: BaseMemory) -> None:
        """Add a memory instance.

        Args:
            memory: Memory instance to add
        """
        self._memories.append(memory)

    def remove(self, memory: BaseMemory) -> None:
        """Remove a memory instance.

        Args:
            memory: Memory instance to remove
        """
        self._memories.remove(memory)

    def get_by_name(self, name: str) -> Optional[BaseMemory]:
        """Get memory by name.

        Args:
            name: Memory name

        Returns:
            Memory instance if found, None otherwise
        """
        for memory in self._memories:
            if memory.name == name:
                return memory
        return None

    def filter(self, filter_fn: Callable[[BaseMemory], bool]) -> List[BaseMemory]:
        """Filter memories by predicate.

        Args:
            filter_fn: Filter function

        Returns:
            List of matching memories
        """
        return [m for m in self._memories if filter_fn(m)]

    def clear_all(self) -> None:
        """Clear all memories."""
        for memory in self._memories:
            memory.clear()

    def save_all(self, path: str) -> None:
        """Save all memories.

        Args:
            path: Base path to save to
        """
        for memory in self._memories:
            memory.save(f"{path}/{memory.name}")

    def load_all(self, path: str) -> None:
        """Load all memories.

        Args:
            path: Base path to load from
        """
        for memory in self._memories:
            memory.load(f"{path}/{memory.name}")
