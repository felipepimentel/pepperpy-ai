"""Base memory provider module.

This module defines the base classes and interfaces for memory providers.
"""

from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from pepperpy.core.common.providers.unified import BaseProvider, ProviderConfig


class MemoryConfig(ProviderConfig):
    """Memory provider configuration.

    Attributes:
        ttl: Time-to-live in seconds (0 for no expiration)
        max_size: Maximum number of items (0 for unlimited)
        eviction_policy: Cache eviction policy
    """

    ttl: Optional[int] = Field(default=None, description="Time to live in seconds")
    max_size: Optional[int] = Field(default=None, description="Maximum size in bytes")


T = TypeVar("T")


class MemoryItem(BaseModel, Generic[T]):
    """Memory item."""

    value: T
    created_at: float
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryProvider(BaseProvider, Generic[T]):
    """Base class for memory providers."""

    config_class = MemoryConfig

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get value by key.

        Args:
            key: Key to get

        Returns:
            Value associated with key
        """
        pass

    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple values by keys.

        Args:
            keys: Keys to get

        Returns:
            Dictionary mapping keys to values
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem[T]:
        """Set value by key.

        Args:
            key: Key to set
            value: Value to set
            ttl: Time to live in seconds
            metadata: Optional metadata

        Returns:
            Memory item
        """
        pass

    @abstractmethod
    async def set_many(
        self,
        items: Dict[str, T],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem[T]]:
        """Set multiple values.

        Args:
            items: Dictionary mapping keys to values
            ttl: Time to live in seconds
            metadata: Optional metadata

        Returns:
            List of memory items
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value by key.

        Args:
            key: Key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple values.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_metadata(self, key: str) -> Optional[MemoryItem[T]]:
        """Get item metadata.

        Args:
            key: Key to get metadata for

        Returns:
            Memory item or None if key does not exist
        """
        pass

    @abstractmethod
    async def update_metadata(
        self, key: str, metadata: Dict[str, Any]
    ) -> Optional[MemoryItem[T]]:
        """Update item metadata.

        Args:
            key: Key to update metadata for
            metadata: New metadata

        Returns:
            Updated memory item or None if key does not exist
        """
        pass

    @abstractmethod
    async def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Pattern to match keys against

        Returns:
            List of matching keys
        """
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key.

        Args:
            key: Key to get TTL for

        Returns:
            Remaining TTL in seconds or None if key does not exist or has no TTL
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values."""
        pass
