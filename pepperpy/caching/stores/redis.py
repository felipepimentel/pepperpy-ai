"""Redis cache store implementation."""

import json
import time
from typing import Any, Dict, Generic, Optional, Set

import redis.asyncio as redis
from redis.asyncio.client import Redis

from pepperpy.caching.errors import CacheBackendError, CacheKeyError
from pepperpy.caching.stores.base import CacheStore
from pepperpy.caching.types import CacheKey, CacheMetadata, CacheTTL, CacheValueType


class RedisStore(CacheStore[CacheValueType], Generic[CacheValueType]):
    """Redis cache store implementation.
    
    This store uses Redis as the backend storage. It supports:
    - Basic key-value operations
    - TTL expiration (using Redis TTL)
    - Metadata storage (as JSON in a separate hash)
    - Policy-based eviction
    
    Attributes:
        prefix: Key prefix for namespacing
        encoding: Character encoding for strings
        serializer: JSON encoder class
        deserializer: JSON decoder class
    """

    def __init__(
        self,
        redis_url: str,
        prefix: str = "pepperpy:",
        encoding: str = "utf-8",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the Redis store.
        
        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for namespacing
            encoding: Character encoding for strings
            *args: Additional arguments for CacheStore
            **kwargs: Additional keyword arguments for CacheStore
            
        Raises:
            CacheBackendError: If Redis connection fails
        """
        super().__init__(*args, **kwargs)
        self.prefix = prefix
        self.encoding = encoding
        
        try:
            self._redis: Redis[bytes] = redis.from_url(redis_url)
            self._metadata_key = f"{self.prefix}metadata"
        except Exception as e:
            raise CacheBackendError(f"Failed to connect to Redis: {e}")

    def _make_key(self, key: CacheKey) -> str:
        """Create a prefixed key for Redis.
        
        Args:
            key: The original cache key
            
        Returns:
            Prefixed key for Redis
        """
        return f"{self.prefix}{key}"

    async def get(
        self,
        key: CacheKey,
        default: Any = None,
    ) -> Optional[CacheValueType]:
        """Get a value from Redis.
        
        Args:
            key: The cache key
            default: Value to return if key not found
            
        Returns:
            The cached value or default if not found
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheBackendError: If there's an error accessing Redis
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        try:
            redis_key = self._make_key(key)
            value = await self._redis.get(redis_key)
            
            if value is None:
                self._track_miss()
                return default
                
            self._track_hit()
            if self.policy and self.policy.update_access_on_get:
                self.policy.update_access(key)
                
            return json.loads(value.decode(self.encoding))
            
        except Exception as e:
            raise CacheBackendError(f"Failed to get value from Redis: {e}")

    async def set(
        self,
        key: CacheKey,
        value: CacheValueType,
        ttl: CacheTTL = None,
        metadata: Optional[CacheMetadata] = None,
    ) -> bool:
        """Store a value in Redis.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
            metadata: Optional metadata to store with the value
            
        Returns:
            True if value was stored successfully
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheBackendError: If there's an error accessing Redis
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        try:
            # Check policy
            if self.policy and not self.policy.should_cache(key, value, metadata):
                # Find a key to evict
                async for k in self._redis.scan_iter(f"{self.prefix}*"):
                    k_str = k.decode(self.encoding).removeprefix(self.prefix)
                    if self.policy.should_evict(k_str, await self.get_metadata(k_str)):
                        await self.delete(k_str)
                        self._track_eviction()
                        break
                else:
                    return False
                    
            redis_key = self._make_key(key)
            value_json = json.dumps(value)
            
            # Store value with TTL if provided
            if ttl is not None:
                await self._redis.setex(redis_key, ttl, value_json)
            else:
                await self._redis.set(redis_key, value_json)
                
            # Store metadata if provided
            if metadata:
                await self._redis.hset(
                    self._metadata_key,
                    redis_key,
                    json.dumps(metadata),
                )
                
            if self.policy:
                self.policy.update_access(key)
                
            self._track_set()
            return True
            
        except Exception as e:
            raise CacheBackendError(f"Failed to set value in Redis: {e}")

    async def delete(self, key: CacheKey) -> bool:
        """Remove a value from Redis.
        
        Args:
            key: The cache key
            
        Returns:
            True if value was deleted successfully
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheBackendError: If there's an error accessing Redis
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        try:
            redis_key = self._make_key(key)
            
            # Delete value and metadata
            deleted = await self._redis.delete(redis_key)
            await self._redis.hdel(self._metadata_key, redis_key)
            
            if deleted:
                if self.policy:
                    self.policy.remove_access(key)
                self._track_delete()
                
            return bool(deleted)
            
        except Exception as e:
            raise CacheBackendError(f"Failed to delete value from Redis: {e}")

    async def clear(self) -> bool:
        """Remove all values from Redis.
        
        Returns:
            True if cache was cleared successfully
            
        Raises:
            CacheBackendError: If there's an error accessing Redis
        """
        try:
            # Delete all keys with prefix
            async for key in self._redis.scan_iter(f"{self.prefix}*"):
                await self._redis.delete(key)
                
            # Delete metadata
            await self._redis.delete(self._metadata_key)
            
            if self.policy:
                for key in list(self.policy._access_times.keys()):
                    self.policy.remove_access(key)
                    
            return True
            
        except Exception as e:
            raise CacheBackendError(f"Failed to clear Redis cache: {e}")

    async def get_metadata(self, key: CacheKey) -> Optional[CacheMetadata]:
        """Get metadata for a cached value.
        
        Args:
            key: The cache key
            
        Returns:
            The metadata dictionary or None if not found
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheBackendError: If there's an error accessing Redis
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        try:
            redis_key = self._make_key(key)
            metadata_json = await self._redis.hget(self._metadata_key, redis_key)
            
            if metadata_json is None:
                return None
                
            return json.loads(metadata_json.decode(self.encoding))
            
        except Exception as e:
            raise CacheBackendError(f"Failed to get metadata from Redis: {e}")

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
            CacheBackendError: If there's an error accessing Redis
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        try:
            redis_key = self._make_key(key)
            
            # Check if value exists
            if not await self._redis.exists(redis_key):
                return False
                
            await self._redis.hset(
                self._metadata_key,
                redis_key,
                json.dumps(metadata),
            )
            return True
            
        except Exception as e:
            raise CacheBackendError(f"Failed to update metadata in Redis: {e}")

    async def contains(self, key: CacheKey) -> bool:
        """Check if a key exists in Redis.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key exists
            
        Raises:
            CacheKeyError: If the key is invalid
            CacheBackendError: If there's an error accessing Redis
        """
        if not isinstance(key, (str, bytes)):
            raise CacheKeyError(key)
            
        try:
            redis_key = self._make_key(key)
            return bool(await self._redis.exists(redis_key))
            
        except Exception as e:
            raise CacheBackendError(f"Failed to check key in Redis: {e}")

    async def get_keys(self) -> Set[CacheKey]:
        """Get all keys in Redis.
        
        Returns:
            Set of all cache keys
            
        Raises:
            CacheBackendError: If there's an error accessing Redis
        """
        try:
            keys = set()
            async for key in self._redis.scan_iter(f"{self.prefix}*"):
                # Remove prefix from keys
                key_str = key.decode(self.encoding)
                if key_str != self._metadata_key:
                    keys.add(key_str.removeprefix(self.prefix))
            return keys
            
        except Exception as e:
            raise CacheBackendError(f"Failed to get keys from Redis: {e}")

    async def get_size(self) -> int:
        """Get the number of items in Redis.
        
        Returns:
            Number of cached items
            
        Raises:
            CacheBackendError: If there's an error accessing Redis
        """
        try:
            count = 0
            async for _ in self._redis.scan_iter(f"{self.prefix}*"):
                count += 1
            return count - 1  # Subtract 1 for metadata key
            
        except Exception as e:
            raise CacheBackendError(f"Failed to get cache size from Redis: {e}")

    async def get_capacity(self) -> Optional[int]:
        """Get the maximum capacity of the cache.
        
        Returns:
            Maximum number of items the cache can hold, or None if unlimited
            
        Raises:
            CacheBackendError: If there's an error accessing Redis
        """
        return self.policy.max_size if self.policy else None 