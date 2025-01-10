"""Cache implementation."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class CacheError(Exception):
    """Base cache error."""

    pass


class Cache(Generic[T], ABC):
    """Base cache interface."""

    @abstractmethod
    async def get(self, key: str) -> T | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise

        Raises:
            CacheError: If get operation fails
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: T) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache

        Raises:
            CacheError: If set operation fails
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key

        Raises:
            CacheError: If delete operation fails
        """
        pass


class MemoryCache(Cache[T]):
    """In-memory cache implementation."""

    def __init__(self) -> None:
        """Initialize cache."""
        self._cache: dict[str, T] = {}

    async def get(self, key: str) -> T | None:
        """Get value from cache."""
        return self._cache.get(key)

    async def set(self, key: str, value: T) -> None:
        """Set value in cache."""
        self._cache[key] = value

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)
