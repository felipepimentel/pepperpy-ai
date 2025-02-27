"""Local cache for performance optimization.

Implements an in-memory local cache system for optimizing
performance in frequent requests.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, TypeVar

T = TypeVar("T")


class LocalCache:
    """Local in-memory cache implementation."""

    def __init__(self, max_size: int = 1000, ttl: Optional[int] = None) -> None:
        """Initialize local cache.

        Args:
            max_size: Maximum number of items to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        self._max_size = max_size
        self._ttl = ttl
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[T]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired
        """
        if key not in self._cache:
            self._misses += 1
            return None

        if self._is_expired(key):
            self._remove(key)
            self._misses += 1
            return None

        self._hits += 1
        return self._cache[key]

    def set(self, key: str, value: T) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if len(self._cache) >= self._max_size:
            self._evict()

        self._cache[key] = value
        self._timestamps[key] = datetime.now()

    def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        self._remove(key)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._timestamps.clear()
        self._hits = 0
        self._misses = 0

    def _is_expired(self, key: str) -> bool:
        """Check if key is expired.

        Args:
            key: Cache key

        Returns:
            True if expired
        """
        if self._ttl is None:
            return False

        age = datetime.now() - self._timestamps[key]
        return age > timedelta(seconds=self._ttl)

    def _remove(self, key: str) -> None:
        """Remove key from cache.

        Args:
            key: Cache key
        """
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def _evict(self) -> None:
        """Evict oldest entry from cache."""
        if not self._timestamps:
            return

        oldest_key = min(self._timestamps.items(), key=lambda x: x[1])[0]
        self._remove(oldest_key)

    @property
    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of cached items
        """
        return len(self._cache)

    @property
    def hit_ratio(self) -> float:
        """Get cache hit ratio.

        Returns:
            Hit ratio (0-1)
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
