"""Cache module."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypedDict

from ..providers.types import ProviderValue


class JsonDict(TypedDict, total=False):
    """JSON dictionary type."""

    str_value: str | None
    int_value: int | None
    float_value: float | None
    bool_value: bool | None


class CacheEntry:
    """Cache entry."""

    def __init__(
        self,
        key: str,
        value: ProviderValue,
        expires_at: datetime | None = None,
        metadata: JsonDict | None = None,
    ) -> None:
        """Initialize cache entry.

        Args:
            key: Cache key
            value: Cache value
            expires_at: Expiration time
            metadata: Additional metadata
        """
        self.key = key
        self.value = value
        self.expires_at = expires_at
        self.metadata = metadata or {}


class Cache(ABC):
    """Cache interface."""

    @abstractmethod
    async def get(self, key: str) -> CacheEntry | None:
        """Get cache entry.

        Args:
            key: Cache key

        Returns:
            Cache entry if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def set(
        self,
        key: str,
        value: ProviderValue,
        expires_at: datetime | None = None,
        metadata: JsonDict | None = None,
    ) -> CacheEntry:
        """Set cache entry.

        Args:
            key: Cache key
            value: Cache value
            expires_at: Expiration time
            metadata: Additional metadata

        Returns:
            Created cache entry
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete cache entry.

        Args:
            key: Cache key
        """
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        raise NotImplementedError
