"""Redis memory store implementation."""

import json
import logging
from typing import Any, Dict, List, Optional

import aioredis

from pepperpy.common.errors import StorageError
from .base import Memory, MemoryStore


logger = logging.getLogger(__name__)


class RedisMemoryStore(MemoryStore):
    """Redis memory store implementation."""
    
    def __init__(
        self,
        name: str,
        redis_url: str,
        max_size: Optional[int] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        """Initialize Redis memory store.
        
        Args:
            name: Store name
            redis_url: Redis connection URL
            max_size: Optional maximum number of memories
            default_ttl: Optional default time-to-live in seconds
        """
        super().__init__(name, max_size, default_ttl)
        self._redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        
    async def initialize(self) -> None:
        """Initialize store."""
        try:
            self._redis = await aioredis.from_url(self._redis_url)
        except Exception as e:
            raise StorageError(f"Failed to connect to Redis: {e}")
            
    async def cleanup(self) -> None:
        """Clean up store."""
        if self._redis:
            await self._redis.close()
            
    async def _add(self, memories: List[Memory]) -> None:
        """Add memories to store.
        
        Args:
            memories: List of memories to add
            
        Raises:
            StorageError: If storage operation fails
        """
        if not self._redis:
            raise StorageError("Redis client not initialized")
            
        try:
            pipeline = self._redis.pipeline()
            
            for memory in memories:
                key = f"{self.name}:{memory.id}"
                value = json.dumps(memory.to_dict())
                
                if memory.expires_at:
                    ttl = int((memory.expires_at - memory.created_at).total_seconds())
                    pipeline.setex(key, ttl, value)
                else:
                    pipeline.set(key, value)
                    
            await pipeline.execute()
            
        except Exception as e:
            raise StorageError(f"Failed to add memories: {e}")
            
    async def _get(self, id: str) -> Optional[Memory]:
        """Get memory by ID.
        
        Args:
            id: Memory ID
            
        Returns:
            Memory if found, None otherwise
            
        Raises:
            StorageError: If storage operation fails
        """
        if not self._redis:
            raise StorageError("Redis client not initialized")
            
        try:
            key = f"{self.name}:{id}"
            value = await self._redis.get(key)
            
            if value is None:
                return None
                
            data = json.loads(value)
            return Memory.from_dict(data)
            
        except Exception as e:
            raise StorageError(f"Failed to get memory: {e}")
            
    async def _search(
        self,
        query: Any,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """Search memories.
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional search filters
            
        Returns:
            List of matching memories
            
        Raises:
            StorageError: If storage operation fails
        """
        if not self._redis:
            raise StorageError("Redis client not initialized")
            
        try:
            pattern = f"{self.name}:*"
            keys = []
            
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
                
            if not keys:
                return []
                
            values = await self._redis.mget(keys)
            memories = []
            
            for value in values:
                if value is None:
                    continue
                    
                data = json.loads(value)
                memory = Memory.from_dict(data)
                
                if filters and not self._matches_filters(memory, filters):
                    continue
                    
                memories.append(memory)
                
            return memories[:limit]
            
        except Exception as e:
            raise StorageError(f"Failed to search memories: {e}")
            
    def _matches_filters(self, memory: Memory, filters: Dict[str, Any]) -> bool:
        """Check if memory matches filters.
        
        Args:
            memory: Memory to check
            filters: Filters to apply
            
        Returns:
            True if memory matches filters, False otherwise
        """
        for key, value in filters.items():
            if key not in memory.metadata or memory.metadata[key] != value:
                return False
        return True
        
    async def _delete(self, ids: List[str]) -> None:
        """Delete memories.
        
        Args:
            ids: List of memory IDs to delete
            
        Raises:
            StorageError: If storage operation fails
        """
        if not self._redis:
            raise StorageError("Redis client not initialized")
            
        try:
            keys = [f"{self.name}:{id}" for id in ids]
            await self._redis.delete(*keys)
            
        except Exception as e:
            raise StorageError(f"Failed to delete memories: {e}")
            
    async def _clear(self) -> None:
        """Clear all memories.
        
        Raises:
            StorageError: If storage operation fails
        """
        if not self._redis:
            raise StorageError("Redis client not initialized")
            
        try:
            pattern = f"{self.name}:*"
            keys = []
            
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
                
            if keys:
                await self._redis.delete(*keys)
                
        except Exception as e:
            raise StorageError(f"Failed to clear memories: {e}")
            
    async def _count(self) -> int:
        """Get number of memories.
        
        Returns:
            Number of memories in store
            
        Raises:
            StorageError: If storage operation fails
        """
        if not self._redis:
            raise StorageError("Redis client not initialized")
            
        try:
            pattern = f"{self.name}:*"
            count = 0
            
            async for _ in self._redis.scan_iter(match=pattern):
                count += 1
                
            return count
            
        except Exception as e:
            raise StorageError(f"Failed to count memories: {e}") 