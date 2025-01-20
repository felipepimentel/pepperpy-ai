"""Redis memory store implementation for Pepperpy."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

import redis
from redis.client import Redis

from ...common.errors import StorageError, MemoryExpiredError
from .base import Memory, MemoryStore

logger = logging.getLogger(__name__)

class RedisMemoryStore(MemoryStore):
    """Redis memory store implementation."""
    
    def __init__(
        self,
        name: str,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_size: Optional[int] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        """Initialize Redis memory store.
        
        Args:
            name: Store name
            host: Redis host (default: localhost)
            port: Redis port (default: 6379)
            db: Redis database number (default: 0)
            password: Optional Redis password
            max_size: Optional maximum number of memories
            default_ttl: Optional default time-to-live in seconds
        """
        super().__init__(name, max_size, default_ttl)
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._client: Optional[Redis] = None
        
    async def _initialize(self) -> None:
        """Initialize Redis client."""
        self._client = redis.Redis(
            host=self._host,
            port=self._port,
            db=self._db,
            password=self._password,
            decode_responses=True,
        )
        logger.debug(f"Connected to Redis at {self._host}:{self._port}")
        
    async def _cleanup(self) -> None:
        """Cleanup Redis client."""
        if self._client is not None:
            self._client.close()
            self._client = None
            
    async def _add(self, memories: List[Memory]) -> None:
        """Add memories to Redis."""
        pipeline = self._client.pipeline()
        
        for memory in memories:
            # Store memory data
            key = f"memory:{memory.id}"
            data = {
                "content": json.dumps(memory.content),
                "metadata": json.dumps(memory.metadata),
                "created_at": memory.created_at.isoformat(),
            }
            pipeline.hmset(key, data)
            
            # Set expiration if needed
            if memory.expires_at is not None:
                ttl = int((memory.expires_at - memory.created_at).total_seconds())
                pipeline.expire(key, ttl)
                
        pipeline.execute()
        logger.debug(f"Added {len(memories)} memories to Redis")
        
    async def _get(self, id: str) -> Optional[Memory]:
        """Get memory from Redis."""
        key = f"memory:{id}"
        data = self._client.hgetall(key)
        
        if not data:
            return None
            
        # Create memory instance
        content = json.loads(data["content"])
        metadata = json.loads(data["metadata"])
        created_at = data["created_at"]
        
        memory = Memory(id=id, content=content, metadata=metadata)
        memory._created_at = created_at
        
        # Get TTL if exists
        ttl = self._client.ttl(key)
        if ttl > 0:
            memory._expires_at = memory.created_at + timedelta(seconds=ttl)
            
        return memory
        
    async def _search(
        self,
        query: Any,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """Search Redis memories."""
        # Get all memory keys
        keys = self._client.keys("memory:*")
        memories = []
        
        # Load memories
        for key in keys:
            id_ = key.split(":", 1)[1]
            memory = await self._get(id_)
            
            if memory is None:
                continue
                
            # Apply filters
            if filters:
                match = True
                for key, value in filters.items():
                    if memory.metadata.get(key) != value:
                        match = False
                        break
                        
                if not match:
                    continue
                    
            memories.append(memory)
            
            if len(memories) >= limit:
                break
                
        return memories
        
    async def _delete(self, ids: List[str]) -> None:
        """Delete memories from Redis."""
        keys = [f"memory:{id_}" for id_ in ids]
        self._client.delete(*keys)
        logger.debug(f"Deleted {len(ids)} memories from Redis")
        
    async def _clear(self) -> None:
        """Clear Redis memories."""
        keys = self._client.keys("memory:*")
        if keys:
            self._client.delete(*keys)
            logger.debug("Cleared all memories from Redis")
            
    async def _count(self) -> int:
        """Count Redis memories."""
        return len(self._client.keys("memory:*"))
        
    def __repr__(self) -> str:
        """Return string representation."""
        count = self._client.dbsize() if self._client else 0
        
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"host={self._host}, "
            f"port={self._port}, "
            f"db={self._db}, "
            f"memories={count}"
            f")"
        ) 