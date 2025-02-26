"""Simple in-memory storage implementation."""

from typing import Any, Dict, List, Optional, TypeVar

from .base import MemoryInterface

T = TypeVar("T")


class SimpleMemory(MemoryInterface[T]):
    """Simple in-memory storage implementation."""

    def __init__(self):
        """Initialize simple memory storage."""
        self._storage: Dict[str, T] = {}
        self._history: List[Dict[str, Any]] = []

    def store(self, key: str, value: T) -> None:
        """Store a value in memory."""
        self._storage[key] = value
        self._history.append({"action": "store", "key": key})

    def retrieve(self, key: str) -> Optional[T]:
        """Retrieve a value from memory."""
        return self._storage.get(key)

    def delete(self, key: str) -> bool:
        """Delete a value from memory."""
        if key in self._storage:
            del self._storage[key]
            self._history.append({"action": "delete", "key": key})
            return True
        return False

    def clear(self) -> None:
        """Clear all values from memory."""
        self._storage.clear()
        self._history.append({"action": "clear"})

    def get_history(self) -> List[Dict[str, Any]]:
        """Get operation history.

        Returns:
            List[Dict[str, Any]]: List of operations performed
        """
        return self._history.copy()

    def exists(self, key: str) -> bool:
        """Check if a key exists in memory.

        Args:
            key: Key to check

        Returns:
            bool: True if key exists, False otherwise
        """
        return key in self._storage

    def list_keys(self) -> List[str]:
        """List all stored keys.

        Returns:
            List[str]: List of stored keys
        """
        return list(self._storage.keys())
