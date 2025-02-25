"""In-memory cache store implementation."""

import time
from typing import Any, Dict, Generic, Optional, Set

from pepperpy.caching.errors import CacheError, CacheKeyError
from pepperpy.caching.stores.base import CacheStore
from pepperpy.caching.types import CacheKey, CacheMetadata, CacheTTL, CacheValueType


class MemoryStore(CacheStore[CacheValueType], Generic[CacheValueType]):
    """In-memory cache store implementation.
    
    This store keeps all data in memory using a dictionary. It supports:
    - Basic key-value operations
    - TTL expiration
    - Metadata storage
    - Policy-based eviction
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the memory store."""
        super().__init__(*args, **kwargs)
        self._data: Dict[CacheKey, CacheValueType] = {}
        self._metadata: Dict[CacheKey, CacheMetadata] = {}
        self._ttls: Dict[CacheKey, float] = {}

    async def get(
        self,
        key: CacheKey,
        default: Any = None,
    ) -> Optional[CacheValueType]:
        """Get a value from the cache.
        
        Args:
            key: The cache key
            default: Value to return if key not found
            
        Returns:
            The cached value or default if not found
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheError: If there's an error accessing the cache
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        # Check TTL expiration
        if key in self._ttls and time.time() > self._ttls[key]:
            await self.delete(key)
            self._track_miss()
            return default
            
        value = self._data.get(key)
        if value is None:
            self._track_miss()
            return default
            
        self._track_hit()
        if self.policy and self.policy.update_access_on_get:
            self.policy.update_access(key)
            
        return value

    async def set(
        self,
        key: CacheKey,
        value: CacheValueType,
        ttl: CacheTTL = None,
        metadata: Optional[CacheMetadata] = None,
    ) -> bool:
        """Store a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
            metadata: Optional metadata to store with the value
            
        Returns:
            True if value was stored successfully
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheError: If there's an error accessing the cache
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        # Check policy
        if self.policy and not self.policy.should_cache(key, value, metadata):
            # Find a key to evict
            for k in self._data:
                if self.policy.should_evict(k, self._metadata.get(k)):
                    await self.delete(k)
                    self._track_eviction()
                    break
            else:
                return False
                
        self._data[key] = value
        if metadata:
            self._metadata[key] = metadata
            
        if ttl is not None:
            self._ttls[key] = time.time() + ttl
            
        if self.policy:
            self.policy.update_access(key)
            
        self._track_set()
        return True

    async def delete(self, key: CacheKey) -> bool:
        """Remove a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if value was deleted successfully
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheError: If there's an error accessing the cache
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        if key not in self._data:
            return False
            
        del self._data[key]
        self._metadata.pop(key, None)
        self._ttls.pop(key, None)
        
        if self.policy:
            self.policy.remove_access(key)
            
        self._track_delete()
        return True

    async def clear(self) -> bool:
        """Remove all values from the cache.
        
        Returns:
            True if cache was cleared successfully
            
        Raises:
            CacheError: If there's an error accessing the cache
        """
        self._data.clear()
        self._metadata.clear()
        self._ttls.clear()
        
        if self.policy:
            for key in list(self.policy._access_times.keys()):
                self.policy.remove_access(key)
                
        return True

    async def get_metadata(self, key: CacheKey) -> Optional[CacheMetadata]:
        """Get metadata for a cached value.
        
        Args:
            key: The cache key
            
        Returns:
            The metadata dictionary or None if not found
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheError: If there's an error accessing the cache
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        return self._metadata.get(key)

    async def update_metadata(
        self,
        key: CacheKey,
        metadata: CacheMetadata,
    ) -> bool:
        """Update metadata for a cached value.
        
        Args:
            key: The cache key
            metadata: New metadata to store
            
        Returns:
            True if metadata was updated successfully
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheError: If there's an error accessing the cache
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        if key not in self._data:
            return False
            
        self._metadata[key] = metadata
        return True

    async def contains(self, key: CacheKey) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key exists
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheError: If there's an error accessing the cache
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        # Check TTL expiration
        if key in self._ttls and time.time() > self._ttls[key]:
            await self.delete(key)
            return False
            
        return key in self._data

    async def get_keys(self) -> Set[CacheKey]:
        """Get all keys in the cache.
        
        Returns:
            Set of all cache keys
            
        Raises:
            CacheError: If there's an error accessing the cache
        """
        # Remove expired keys
        for key in list(self._ttls.keys()):
            if time.time() > self._ttls[key]:
                await self.delete(key)
                
        return set(self._data.keys())

    async def get_size(self) -> int:
        """Get the number of items in the cache.
        
        Returns:
            Number of cached items
            
        Raises:
            CacheError: If there's an error accessing the cache
        """
        return len(self._data)

    async def get_capacity(self) -> Optional[int]:
        """Get the maximum capacity of the cache.
        
        Returns:
            Maximum number of items the cache can hold, or None if unlimited
            
        Raises:
            CacheError: If there's an error accessing the cache
        """
        return self.policy.max_size if self.policy else None 