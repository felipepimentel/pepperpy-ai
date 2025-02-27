"""In-memory cache implementation for the unified caching system.

This module provides an in-memory cache implementation with:
- Thread-safe operations
- TTL support
- LRU/LFU eviction policies
- Metrics collection
"""

import asyncio
import random
from datetime import timedelta
from typing import Dict, List, Optional, Union

from .base import (
    CacheBackend,
    CacheEntry,
    CachePolicy,
    CachePolicyType,
    PolicyError,
    T,
)


class LRUPolicy(CachePolicy):
    """Least Recently Used eviction policy."""

    @property
    def policy_type(self) -> CachePolicyType:
        """Get the policy type.

        Returns:
            LRU policy type
        """
        return CachePolicyType.LRU

    def select_entries_to_evict(
        self, entries: Dict[str, CacheEntry], count: int = 1
    ) -> List[str]:
        """Select least recently used entries to evict.

        Args:
            entries: Dictionary of cache entries
            count: Number of entries to select

        Returns:
            List of keys to evict
        """
        if not entries:
            return []

        # Sort by last accessed time (oldest first)
        sorted_entries = sorted(entries.items(), key=lambda item: item[1].last_accessed)

        # Return the oldest entries up to count
        return [key for key, _ in sorted_entries[:count]]


class LFUPolicy(CachePolicy):
    """Least Frequently Used eviction policy."""

    @property
    def policy_type(self) -> CachePolicyType:
        """Get the policy type.

        Returns:
            LFU policy type
        """
        return CachePolicyType.LFU

    def select_entries_to_evict(
        self, entries: Dict[str, CacheEntry], count: int = 1
    ) -> List[str]:
        """Select least frequently used entries to evict.

        Args:
            entries: Dictionary of cache entries
            count: Number of entries to select

        Returns:
            List of keys to evict
        """
        if not entries:
            return []

        # Sort by access count (least accessed first)
        sorted_entries = sorted(entries.items(), key=lambda item: item[1].access_count)

        # Return the least accessed entries up to count
        return [key for key, _ in sorted_entries[:count]]


class FIFOPolicy(CachePolicy):
    """First In First Out eviction policy."""

    @property
    def policy_type(self) -> CachePolicyType:
        """Get the policy type.

        Returns:
            FIFO policy type
        """
        return CachePolicyType.FIFO

    def select_entries_to_evict(
        self, entries: Dict[str, CacheEntry], count: int = 1
    ) -> List[str]:
        """Select oldest entries to evict.

        Args:
            entries: Dictionary of cache entries
            count: Number of entries to select

        Returns:
            List of keys to evict
        """
        if not entries:
            return []

        # Sort by creation time (oldest first)
        sorted_entries = sorted(entries.items(), key=lambda item: item[1].created_at)

        # Return the oldest entries up to count
        return [key for key, _ in sorted_entries[:count]]


class RandomPolicy(CachePolicy):
    """Random eviction policy."""

    @property
    def policy_type(self) -> CachePolicyType:
        """Get the policy type.

        Returns:
            Random policy type
        """
        return CachePolicyType.RANDOM

    def select_entries_to_evict(
        self, entries: Dict[str, CacheEntry], count: int = 1
    ) -> List[str]:
        """Select random entries to evict.

        Args:
            entries: Dictionary of cache entries
            count: Number of entries to select

        Returns:
            List of keys to evict
        """
        if not entries:
            return []

        # Get all keys
        keys = list(entries.keys())

        # Select random keys up to count
        count = min(count, len(keys))
        return random.sample(keys, count)


class MemoryCache(CacheBackend[T]):
    """In-memory cache implementation with TTL and policy support."""

    def __init__(
        self,
        max_size: int = 1000,
        policy: Optional[CachePolicy] = None,
        cleanup_interval: int = 60,
    ):
        """Initialize memory cache.

        Args:
            max_size: Maximum number of items to cache
            policy: Optional eviction policy (defaults to LRU)
            cleanup_interval: Interval in seconds for expired entry cleanup
        """
        super().__init__()
        self._max_size = max_size
        self._policy = policy or LRUPolicy()
        self._cleanup_interval = cleanup_interval
        self._entries: Dict[str, CacheEntry[T]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._hits = 0
        self._misses = 0

        # Start cleanup task
        self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        try:
            while True:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            # Log the error but don't crash
            print(f"Error in cache cleanup task: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove all expired entries."""
        async with self._lock:
            # Find expired keys
            expired_keys = [
                key for key, entry in self._entries.items() if entry.is_expired()
            ]

            # Remove expired entries
            for key in expired_keys:
                del self._entries[key]

    async def _evict(self, count: int = 1) -> None:
        """Evict entries based on policy.

        Args:
            count: Number of entries to evict
        """
        try:
            # Get keys to evict
            keys_to_evict = self._policy.select_entries_to_evict(self._entries, count)

            # Remove entries
            for key in keys_to_evict:
                del self._entries[key]

        except Exception as e:
            raise PolicyError(f"Failed to evict entries: {e}")

    async def get(self, key: str) -> Optional[T]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        async with self._lock:
            entry = self._entries.get(key)

            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired():
                del self._entries[key]
                self._misses += 1
                return None

            # Update access metadata
            entry.touch()
            self._hits += 1

            return entry.value

    async def set(
        self, key: str, value: T, ttl: Optional[Union[int, timedelta]] = None
    ) -> None:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live (seconds or timedelta)
        """
        async with self._lock:
            # Check if we need to evict entries
            if key not in self._entries and len(self._entries) >= self._max_size:
                await self._evict(1)

            # Create entry
            expires_at = self._convert_ttl(ttl)
            entry = CacheEntry(
                key=key,
                value=value,
                expires_at=expires_at,
            )

            # Store entry
            self._entries[key] = entry

    async def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if key in self._entries:
                del self._entries[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all values from cache."""
        async with self._lock:
            self._entries.clear()
            self._hits = 0
            self._misses = 0

    async def contains(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists and not expired, False otherwise
        """
        async with self._lock:
            entry = self._entries.get(key)

            if entry is None:
                return False

            if entry.is_expired():
                del self._entries[key]
                return False

            return True

    @property
    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of cached items
        """
        return len(self._entries)

    @property
    def hit_ratio(self) -> float:
        """Get cache hit ratio.

        Returns:
            Hit ratio (0-1)
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def __del__(self) -> None:
        """Clean up resources when object is deleted."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
