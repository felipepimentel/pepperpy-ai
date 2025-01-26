"""Redis memory provider implementation."""

import json
import logging
from typing import Any, Dict, List, Optional, cast

import redis.asyncio as redis

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.providers.memory.base import BaseMemoryProvider
from ..base.provider import BaseProvider, ProviderConfig


logger = logging.getLogger(__name__)


class RedisMemoryError(PepperpyError):
    """Redis memory provider error."""
    pass


class KeyManager:
    """Helper class for managing Redis keys."""
    
    def __init__(self, prefix: str):
        """Initialize key manager."""
        self.prefix = prefix
    
    def get_key(self, key: str) -> str:
        """Get the full key with prefix."""
        return f"{self.prefix}{key}"
    
    def remove_prefix(self, key: str) -> str:
        """Remove prefix from key."""
        return key.removeprefix(self.prefix)
    
    async def scan_keys(
        self,
        client: redis.Redis[str],
        pattern: str
    ) -> List[str]:
        """Scan for keys matching pattern."""
        keys = []
        cursor = 0
        while True:
            cursor, batch = await client.scan(cursor, match=pattern)
            keys.extend(self.remove_prefix(k) for k in batch)
            if cursor == 0:
                break
        return keys


class DataSerializer:
    """Helper class for data serialization."""
    
    @staticmethod
    def serialize(value: Any) -> str:
        """Serialize value to string."""
        return json.dumps(value)
    
    @staticmethod
    def deserialize(value: Optional[str]) -> Optional[Any]:
        """Deserialize value from string."""
        return json.loads(value) if value else None


@BaseMemoryProvider.register("redis")
class RedisMemoryProvider(BaseMemoryProvider):
    """Redis memory provider implementation.
    
    This provider uses Redis as a backend for storing and retrieving
    memory data.
    """
    
    def __init__(self, config: ProviderConfig):
        """Initialize the Redis memory provider."""
        super().__init__(config)
        self.client: Optional[redis.Redis[str]] = None
        self.key_manager = KeyManager(config.parameters.get("prefix", "pepperpy:"))
        self.serializer = DataSerializer()
        self.ttl = config.parameters.get("ttl", None)  # None means no expiration
    
    async def initialize(self) -> None:
        """Initialize the Redis client."""
        if not self._initialized:
            host = self.config.parameters.get("host", "localhost")
            port = self.config.parameters.get("port", 6379)
            db = self.config.parameters.get("db", 0)
            password = self.config.parameters.get("password")
            
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True
            )
            
            # Test connection
            await self.client.ping()
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.client:
            await self.client.close()
            self._initialized = False
    
    def _get_client(self) -> redis.Redis[str]:
        """Get Redis client with proper type checking."""
        if not self._initialized or not self.client:
            raise RedisMemoryError("Provider not initialized")
        return self.client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        client = self._get_client()
        value = await client.get(self.key_manager.get_key(key))
        return self.serializer.deserialize(value)
    
    async def set(self, key: str, value: Any) -> None:
        """Set value in Redis."""
        client = self._get_client()
        serialized = self.serializer.serialize(value)
        await client.set(
            self.key_manager.get_key(key),
            serialized,
            ex=self.ttl
        )
    
    async def delete(self, key: str) -> None:
        """Delete value from Redis."""
        client = self._get_client()
        await client.delete(self.key_manager.get_key(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        client = self._get_client()
        return await client.exists(self.key_manager.get_key(key)) > 0
    
    async def clear(self) -> None:
        """Clear all values with prefix."""
        client = self._get_client()
        pattern = f"{self.key_manager.prefix}*"
        keys = await self.key_manager.scan_keys(client, pattern)
        if keys:
            await client.delete(*[self.key_manager.get_key(k) for k in keys])
    
    async def list_keys(self) -> List[str]:
        """List all keys with prefix."""
        client = self._get_client()
        pattern = f"{self.key_manager.prefix}*"
        return await self.key_manager.scan_keys(client, pattern)
    
    async def store(self, key: str, value: Any) -> None:
        """Store value in Redis.
        
        Args:
            key: Storage key
            value: Value to store
            
        Raises:
            RedisMemoryError: If value cannot be stored
        """
        try:
            client = self._get_client()
            serialized = self.serializer.serialize(value)
            await client.set(
                self.key_manager.get_key(key),
                serialized,
                ex=self.ttl
            )
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
        try:
            client = self._get_client()
            value = await client.get(self.key_manager.get_key(key))
            return self.serializer.deserialize(value)
        except Exception as e:
            raise RedisMemoryError(f"Failed to retrieve value: {e}") 