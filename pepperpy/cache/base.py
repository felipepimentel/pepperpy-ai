"""
PepperPy Cache Base Module.

Base interfaces and abstractions for cache functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, TypeVar, runtime_checkable

from pepperpy.core.errors import PepperpyError

T = TypeVar("T")


class CacheError(PepperpyError):
    """Base exception for cache-related errors."""

    pass


@runtime_checkable
class CacheProvider(Protocol):
    """Protocol for cache providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the cache provider."""
        ...

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live in seconds
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the cache."""
        ...

    @abstractmethod
    async def has(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        ...

    @abstractmethod
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of cache keys to values (only for keys that exist)
        """
        ...

    @abstractmethod
    async def set_many(self, items: dict[str, Any], ttl: int | None = None) -> None:
        """Set multiple values in the cache.

        Args:
            items: Dictionary of cache keys to values
            ttl: Optional time-to-live in seconds
        """
        ...

    @abstractmethod
    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Number of keys deleted
        """
        ...


class BaseCacheProvider(ABC):
    """Base implementation for cache providers."""

    def __init__(
        self,
        namespace: str = "default",
        ttl: int | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize base cache provider.

        Args:
            namespace: Cache namespace for segmentation
            ttl: Default TTL for cache entries in seconds
            config: Optional configuration
        """
        self.namespace = namespace
        self.default_ttl = ttl
        self.config = config or {}
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the cache provider.

        Implementations should set self.initialized to True when complete.
        """
        self.initialized = True

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.initialized:
            await self.initialize()
        return None

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live in seconds
        """
        if not self.initialized:
            await self.initialize()

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if not self.initialized:
            await self.initialize()
        return False

    async def has(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.initialized:
            await self.initialize()
        return await self.exists(key)

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.initialized:
            await self.initialize()
        return False

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the cache."""
        if not self.initialized:
            await self.initialize()

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of cache keys to values (only for keys that exist)
        """
        if not self.initialized:
            await self.initialize()

        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value

        return result

    async def set_many(self, items: dict[str, Any], ttl: int | None = None) -> None:
        """Set multiple values in the cache.

        Args:
            items: Dictionary of cache keys to values
            ttl: Optional time-to-live in seconds
        """
        if not self.initialized:
            await self.initialize()

        for key, value in items.items():
            await self.set(key, value, ttl)

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Number of keys deleted
        """
        if not self.initialized:
            await self.initialize()

        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1

        return count

    def make_key(self, key: str) -> str:
        """Create a namespaced key.

        Args:
            key: Original key

        Returns:
            Namespaced key
        """
        return f"{self.namespace}:{key}"
