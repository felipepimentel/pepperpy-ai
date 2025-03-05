"""Memory cache implementation.

This module provides a memory-based cache implementation.
"""

import pickle
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.caching.base import (
    Cache,
    CacheBackend,
    CacheEntry,
    CachePolicy,
    CachePolicyType,
    Serializer,
)

T = TypeVar("T")


class PickleSerializer(Serializer):
    """Pickle-based serializer."""

    def serialize(self, obj: Any) -> bytes:
        """Serialize object to bytes using pickle."""
        return pickle.dumps(obj)

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to object using pickle."""
        return pickle.loads(data)


class FIFOPolicy(CachePolicy):
    """First-in-first-out cache eviction policy."""

    @property
    def policy_type(self) -> CachePolicyType:
        """Get policy type.

        Returns:
            Policy type
        """
        return CachePolicyType.FIFO

    def select_entries_to_evict(
        self, entries: Dict[str, CacheEntry], count: int = 1
    ) -> List[str]:
        """Select entries to evict based on FIFO policy.

        Args:
            entries: Dictionary of cache entries
            count: Number of entries to select

        Returns:
            List of keys to evict
        """
        sorted_entries = sorted(entries.items(), key=lambda item: item[1].created_at)
        return [key for key, _ in sorted_entries[:count]]


class LRUPolicy(CachePolicy):
    """Least-recently-used cache eviction policy."""

    @property
    def policy_type(self) -> CachePolicyType:
        """Get policy type.

        Returns:
            Policy type
        """
        return CachePolicyType.LRU

    def select_entries_to_evict(
        self, entries: Dict[str, CacheEntry], count: int = 1
    ) -> List[str]:
        """Select entries to evict based on LRU policy.

        Args:
            entries: Dictionary of cache entries
            count: Number of entries to select

        Returns:
            List of keys to evict
        """
        sorted_entries = sorted(entries.items(), key=lambda item: item[1].last_accessed)
        return [key for key, _ in sorted_entries[:count]]


class LFUPolicy(CachePolicy):
    """Least-frequently-used cache eviction policy."""

    @property
    def policy_type(self) -> CachePolicyType:
        """Get policy type.

        Returns:
            Policy type
        """
        return CachePolicyType.LFU

    def select_entries_to_evict(
        self, entries: Dict[str, CacheEntry], count: int = 1
    ) -> List[str]:
        """Select entries to evict based on LFU policy.

        Args:
            entries: Dictionary of cache entries
            count: Number of entries to select

        Returns:
            List of keys to evict
        """
        sorted_entries = sorted(entries.items(), key=lambda item: item[1].access_count)
        return [key for key, _ in sorted_entries[:count]]


class RandomPolicy(CachePolicy):
    """Random cache eviction policy."""

    @property
    def policy_type(self) -> CachePolicyType:
        """Get policy type.

        Returns:
            Policy type
        """
        return CachePolicyType.RANDOM

    def select_entries_to_evict(
        self, entries: Dict[str, CacheEntry], count: int = 1
    ) -> List[str]:
        """Select entries to evict based on random policy.

        Args:
            entries: Dictionary of cache entries
            count: Number of entries to select

        Returns:
            List of keys to evict
        """
        keys = list(entries.keys())
        if len(keys) <= count:
            return keys
        return random.sample(keys, count)


class MemoryCache(Cache):
    """In-memory cache implementation."""

    def __init__(self, serializer: Optional[Serializer] = None):
        """Initialize memory cache.

        Args:
            serializer: Optional serializer to use for values
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._serializer = serializer or PickleSerializer()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        entry = self._cache.get(key)
        if entry is None:
            return None

        if entry.is_expired():
            await self.delete(key)
            return None

        entry.touch()  # Update access time and count

        if self._serializer and entry.value is not None:
            return self._serializer.deserialize(entry.value)
        return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live
        """
        if self._serializer:
            value = self._serializer.serialize(value)

        expires_at = None
        if ttl is not None:
            expires_at = datetime.utcnow() + ttl

        self._cache[key] = CacheEntry(key=key, value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if value was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear(self) -> None:
        """Clear all values from cache."""
        self._cache.clear()

    async def has(self, key: str) -> bool:
        """Check if key exists in cache and is not expired.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired, False otherwise
        """
        entry = self._cache.get(key)
        if entry is None:
            return False

        if entry.is_expired():
            await self.delete(key)
            return False

        return True

    # Alias for contains to match the Cache interface
    async def contains(self, key: str) -> bool:
        """Check if key exists in cache and is not expired.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired, False otherwise
        """
        return await self.has(key)


__all__ = [
    "CacheBackend",
    "CacheEntry",
    "FIFOPolicy",
    "LFUPolicy",
    "LRUPolicy",
    "MemoryCache",
    "PickleSerializer",
    "RandomPolicy",
    "Serializer",
]
