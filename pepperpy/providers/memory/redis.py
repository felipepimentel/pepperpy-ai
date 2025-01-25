"""Redis memory provider implementation."""

import json
import logging
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.providers.memory.base import BaseMemoryProvider


logger = logging.getLogger(__name__)


class RedisMemoryError(PepperpyError):
    """Redis memory provider error."""
    pass


@BaseMemoryProvider.register("redis")
class RedisMemoryProvider(BaseMemoryProvider):
    """Redis memory provider implementation.
    
    This provider uses Redis as a backend for storing and retrieving
    memory data.
    """
    
    def __init__(
        self,
        name: str,
        redis_url: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize Redis memory provider.
        
        Args:
            name: Provider name
            redis_url: Redis connection URL
            config: Optional configuration
        """
        super().__init__(name, config)
        self._redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        
    async def _initialize_impl(self) -> None:
        """Initialize Redis client.
        
        Raises:
            RedisMemoryError: If Redis client initialization fails
        """
        try:
            self._redis = await redis.from_url(self._redis_url)
        except Exception as e:
            raise RedisMemoryError(f"Failed to connect to Redis: {e}")
            
    async def _cleanup_impl(self) -> None:
        """Clean up Redis client.
        
        Raises:
            RedisMemoryError: If Redis client cleanup fails
        """
        if self._redis:
            try:
                await self._redis.close()
            except Exception as e:
                raise RedisMemoryError(f"Failed to close Redis connection: {e}")
            
    def _validate_impl(self) -> None:
        """Validate Redis configuration.
        
        Raises:
            RedisMemoryError: If configuration is invalid
        """
        if not self._redis_url:
            raise RedisMemoryError("Redis URL not configured")
            
    async def store(self, key: str, value: Any) -> None:
        """Store value in Redis.
        
        Args:
            key: Storage key
            value: Value to store
            
        Raises:
            RedisMemoryError: If value cannot be stored
        """
        if not self._redis:
            raise RedisMemoryError("Redis client not initialized")
            
        try:
            serialized = json.dumps(value)
            await self._redis.set(f"{self.name}:{key}", serialized)
        except Exception as e:
            raise RedisMemoryError(f"Failed to store value: {e}")
            
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis.
        
        Args:
            key: Storage key
            
        Returns:
            Retrieved value or None if not found
            
        Raises:
            RedisMemoryError: If value cannot be retrieved
        """
        if not self._redis:
            raise RedisMemoryError("Redis client not initialized")
            
        try:
            value = await self._redis.get(f"{self.name}:{key}")
            if value is None:
                return None
                
            return json.loads(value)
        except Exception as e:
            raise RedisMemoryError(f"Failed to retrieve value: {e}")
            
    async def delete(self, key: str) -> None:
        """Delete value from Redis.
        
        Args:
            key: Storage key
            
        Raises:
            RedisMemoryError: If value cannot be deleted
        """
        if not self._redis:
            raise RedisMemoryError("Redis client not initialized")
            
        try:
            await self._redis.delete(f"{self.name}:{key}")
        except Exception as e:
            raise RedisMemoryError(f"Failed to delete value: {e}")
            
    async def clear(self) -> None:
        """Clear all values from Redis.
        
        Raises:
            RedisMemoryError: If values cannot be cleared
        """
        if not self._redis:
            raise RedisMemoryError("Redis client not initialized")
            
        try:
            pattern = f"{self.name}:*"
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            raise RedisMemoryError(f"Failed to clear values: {e}")
            
    async def list_keys(self) -> List[str]:
        """List all keys in Redis.
        
        Returns:
            List of storage keys
            
        Raises:
            RedisMemoryError: If keys cannot be listed
        """
        if not self._redis:
            raise RedisMemoryError("Redis client not initialized")
            
        try:
            pattern = f"{self.name}:*"
            keys = []
            cursor = 0
            while True:
                cursor, batch = await self._redis.scan(cursor, match=pattern)
                keys.extend(k.decode().removeprefix(f"{self.name}:") for k in batch)
                if cursor == 0:
                    break
            return keys
        except Exception as e:
            raise RedisMemoryError(f"Failed to list keys: {e}") 