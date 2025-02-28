"""Base memory provider module.

This module defines the base classes and interfaces for memory providers.
"""

from abc import abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from pepperpy.core.common.providers.unified import BaseProvider, ProviderConfig


class MemoryConfig(ProviderConfig):
    """Memory provider configuration.

    Attributes:
        ttl: Time-to-live in seconds (0 for no expiration)
        max_size: Maximum number of items (0 for unlimited)
        eviction_policy: Cache eviction policy
    """

    ttl: int | None = Field(default=None, description="Time to live in seconds")
    max_size: int | None = Field(default=None, description="Maximum size in bytes")


T = TypeVar("T")


class MemoryItem(BaseModel, Generic[T]):
    """Memory item."""

    value: T
    created_at: float
    expires_at: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryProvider(BaseProvider, Generic[T]):
    """Base class for memory providers."""

    config_class = MemoryConfig

    @abstractmethod
    async def get(self, key: str) -> T | None:
        """Get value by key.

        Args:
            key: Key to get

        Returns:
            Value associated with key
        """
        pass

    @abstractmethod
    async def get_many(self, keys: list[str]) -> dict[str, T]:
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
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
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
        items: dict[str, T],
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[MemoryItem[T]]:
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
    async def delete_many(self, keys: list[str]) -> int:
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
    async def get_metadata(self, key: str) -> MemoryItem[T] | None:
        """Get item metadata.

        Args:
            key: Key to get metadata for

        Returns:
            Memory item or None if key does not exist
        """
        pass

    @abstractmethod
    async def update_metadata(
        self, key: str, metadata: dict[str, Any]
    ) -> MemoryItem[T] | None:
        """Update item metadata.

        Args:
            key: Key to update metadata for
            metadata: New metadata

        Returns:
            Updated memory item or None if key does not exist
        """
        pass

    @abstractmethod
    async def get_keys(self, pattern: str | None = None) -> list[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Pattern to match keys against

        Returns:
            List of matching keys
        """
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> int | None:
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
