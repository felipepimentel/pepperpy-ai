"""Políticas de cache para otimização de performance.

Implementa políticas de cache para gerenciar o ciclo de vida e comportamento
do cache, incluindo estratégias de expiração e evicção.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, TypeVar

T = TypeVar("T")


class CachePolicy(ABC):
    """Base class for cache policies."""

    @abstractmethod
    def should_cache(self, key: str, value: Any) -> bool:
        """Check if value should be cached.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if value should be cached
        """
        pass

    @abstractmethod
    def should_evict(self, key: str, value: Any) -> bool:
        """Check if value should be evicted.

        Args:
            key: Cache key
            value: Cached value

        Returns:
            True if value should be evicted
        """
        pass


class TTLPolicy(CachePolicy):
    """Time-to-live based cache policy."""

    def __init__(self, ttl: int) -> None:
        """Initialize TTL policy.

        Args:
            ttl: Time to live in seconds
        """
        self.ttl = ttl
        self._timestamps: Dict[str, datetime] = {}

    def should_cache(self, key: str, value: Any) -> bool:
        """Check if value should be cached.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if value should be cached
        """
        self._timestamps[key] = datetime.now()
        return True

    def should_evict(self, key: str, value: Any) -> bool:
        """Check if value should be evicted.

        Args:
            key: Cache key
            value: Cached value

        Returns:
            True if value should be evicted
        """
        if key not in self._timestamps:
            return True

        age = datetime.now() - self._timestamps[key]
        return age > timedelta(seconds=self.ttl)


class SizePolicy(CachePolicy):
    """Size-based cache policy."""

    def __init__(self, max_size: int) -> None:
        """Initialize size policy.

        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self._size = 0

    def should_cache(self, key: str, value: Any) -> bool:
        """Check if value should be cached.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if value should be cached
        """
        return self._size < self.max_size

    def should_evict(self, key: str, value: Any) -> bool:
        """Check if value should be evicted.

        Args:
            key: Cache key
            value: Cached value

        Returns:
            True if value should be evicted
        """
        return self._size >= self.max_size


class CompositePolicy(CachePolicy):
    """Composite cache policy combining multiple policies."""

    def __init__(self, policies: List[CachePolicy]) -> None:
        """Initialize composite policy.

        Args:
            policies: List of policies to combine
        """
        self.policies = policies

    def should_cache(self, key: str, value: Any) -> bool:
        """Check if value should be cached.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if all policies allow caching
        """
        return all(p.should_cache(key, value) for p in self.policies)

    def should_evict(self, key: str, value: Any) -> bool:
        """Check if value should be evicted.

        Args:
            key: Cache key
            value: Cached value

        Returns:
            True if any policy requires eviction
        """
        return any(p.should_evict(key, value) for p in self.policies)
