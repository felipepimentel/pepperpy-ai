"""Redis-based memory backend implementation."""

import json
import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis

from ...common.errors import PepperpyError
from ..base import MemoryBackend


logger = logging.getLogger(__name__)


class MemoryError(PepperpyError):
    """Memory error."""
    pass


class RedisBackend(MemoryBackend):
    """Redis-based memory backend implementation."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "pepperpy:memory:",
        **kwargs: Any,
    ) -> None:
        """Initialize Redis backend.
        
        Args:
            host: Redis host (default: localhost)
            port: Redis port (default: 6379)
            db: Redis database number (default: 0)
            password: Optional Redis password
            prefix: Key prefix (default: pepperpy:memory:)
            **kwargs: Additional Redis connection parameters
        """
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._prefix = prefix
        self._kwargs = kwargs
        self._client: Optional[redis.Redis] = None
        
    async def initialize(self) -> None:
        """Initialize backend.
        
        Raises:
            MemoryError: If backend cannot be initialized
        """
        try:
            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                decode_responses=True,
                **self._kwargs,
            )
            await self._client.ping()
            
        except Exception as e:
            raise MemoryError(f"Failed to initialize Redis backend: {e}") from e
            
    async def cleanup(self) -> None:
        """Clean up backend.
        
        Raises:
            MemoryError: If backend cannot be cleaned up
        """
        try:
            if self._client:
                await self._client.close()
                self._client = None
                
        except Exception as e:
            raise MemoryError(f"Failed to clean up Redis backend: {e}") from e
            
    async def store(self, key: str, value: Any) -> None:
        """Store value.
        
        Args:
            key: Storage key
            value: Value to store
            
        Raises:
            MemoryError: If value cannot be stored
        """
        if not self._client:
            raise MemoryError("Redis backend not initialized")
            
        try:
            # Serialize value
            data = json.dumps(value)
            
            # Store in Redis
            await self._client.set(self._prefix + key, data)
            
        except Exception as e:
            raise MemoryError(f"Failed to store value: {e}") from e
            
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value.
        
        Args:
            key: Storage key
            
        Returns:
            Retrieved value or None if not found
            
        Raises:
            MemoryError: If value cannot be retrieved
        """
        if not self._client:
            raise MemoryError("Redis backend not initialized")
            
        try:
            # Get from Redis
            data = await self._client.get(self._prefix + key)
            if not data:
                return None
                
            # Deserialize value
            return json.loads(data)
            
        except Exception as e:
            raise MemoryError(f"Failed to retrieve value: {e}") from e
            
    async def delete(self, key: str) -> None:
        """Delete value.
        
        Args:
            key: Storage key
            
        Raises:
            MemoryError: If value cannot be deleted
        """
        if not self._client:
            raise MemoryError("Redis backend not initialized")
            
        try:
            await self._client.delete(self._prefix + key)
            
        except Exception as e:
            raise MemoryError(f"Failed to delete value: {e}") from e
            
    async def clear(self) -> None:
        """Clear all values.
        
        Raises:
            MemoryError: If values cannot be cleared
        """
        if not self._client:
            raise MemoryError("Redis backend not initialized")
            
        try:
            # Get all keys with prefix
            pattern = self._prefix + "*"
            keys = []
            async for key in self._client.scan_iter(pattern):
                keys.append(key)
                
            # Delete all keys
            if keys:
                await self._client.delete(*keys)
                
        except Exception as e:
            raise MemoryError(f"Failed to clear values: {e}") from e 