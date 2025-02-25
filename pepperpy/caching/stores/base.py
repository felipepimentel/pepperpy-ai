"""Base cache store interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Set

from pepperpy.caching.base import CacheBackend
from pepperpy.caching.errors import CacheError
from pepperpy.caching.policies.base import CachePolicy
from pepperpy.caching.types import CacheKey, CacheMetadata, CacheTTL, CacheValueType


class CacheStore(CacheBackend[CacheValueType], Generic[CacheValueType]):
    """Abstract base class for cache stores.
    
    Cache stores provide the actual storage implementation for cached values.
    They handle the low-level details of storing and retrieving data while
    enforcing policies and collecting metrics.
    """

    def __init__(
        self,
        policy: Optional[CachePolicy[CacheValueType]] = None,
    ) -> None:
        """Initialize the cache store.
        
        Args:
            policy: Optional cache policy to use
        """
        self._policy = policy
        self._stats: Dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }

    @property
    def policy(self) -> Optional[CachePolicy[CacheValueType]]:
        """Get the current cache policy."""
        return self._policy

    @policy.setter
    def policy(self, policy: Optional[CachePolicy[CacheValueType]]) -> None:
        """Set the cache policy.
        
        Args:
            policy: The new cache policy to use
        """
        self._policy = policy

    @abstractmethod
    async def contains(self, key: CacheKey) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key exists
            
        Raises:
            CacheError: If there's an error accessing the cache
        """
        pass

    @abstractmethod
    async def get_keys(self) -> Set[CacheKey]:
        """Get all keys in the cache.
        
        Returns:
            Set of all cache keys
            
        Raises:
            CacheError: If there's an error accessing the cache
        """
        pass

    @abstractmethod
    async def get_size(self) -> int:
        """Get the number of items in the cache.
        
        Returns:
            Number of cached items
            
        Raises:
            CacheError: If there's an error accessing the cache
        """
        pass

    @abstractmethod
    async def get_capacity(self) -> Optional[int]:
        """Get the maximum capacity of the cache.
        
        Returns:
            Maximum number of items the cache can hold, or None if unlimited
            
        Raises:
            CacheError: If there's an error accessing the cache
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary containing:
            - hits: Number of cache hits
            - misses: Number of cache misses
            - sets: Number of set operations
            - deletes: Number of delete operations
            - evictions: Number of evicted items
            - hit_ratio: Cache hit ratio (hits / total accesses)
        """
        total = self._stats["hits"] + self._stats["misses"]
        hit_ratio = self._stats["hits"] / total if total > 0 else 0.0
        
        return {
            **self._stats,
            "hit_ratio": hit_ratio,
        }

    def _track_hit(self) -> None:
        """Track a cache hit."""
        self._stats["hits"] += 1

    def _track_miss(self) -> None:
        """Track a cache miss."""
        self._stats["misses"] += 1

    def _track_set(self) -> None:
        """Track a set operation."""
        self._stats["sets"] += 1

    def _track_delete(self) -> None:
        """Track a delete operation."""
        self._stats["deletes"] += 1

    def _track_eviction(self) -> None:
        """Track a cache eviction."""
        self._stats["evictions"] += 1 