"""Memory provider interfaces and base classes."""

from abc import abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from .base import Provider


class MemoryItem(BaseModel):
    """Base class for memory items."""

    key: str
    value: Any
    created_at: datetime = datetime.utcnow()
    expires_at: datetime | None = None
    metadata: dict[str, Any] = {}


class MemoryProvider(Provider):
    """Base class for memory providers."""

    @abstractmethod
    async def get(self, key: str) -> MemoryItem | None:
        """Get item from memory.

        Args:
            key: Item key

        Returns:
            Optional[MemoryItem]: Item if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryItem:
        """Set item in memory.

        Args:
            key: Item key
            value: Item value
            expires_at: Optional expiration time
            metadata: Optional metadata

        Returns:
            MemoryItem: Created memory item
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete item from memory.

        Args:
            key: Item key

        Returns:
            bool: True if item was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if item exists in memory.

        Args:
            key: Item key

        Returns:
            bool: True if item exists, False otherwise
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all items from memory."""
        pass

    @abstractmethod
    async def keys(self, pattern: str | None = None) -> list[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Optional pattern to match keys against

        Returns:
            List[str]: List of matching keys
        """
        pass
