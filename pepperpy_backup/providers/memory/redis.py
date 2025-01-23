"""Redis memory provider implementation."""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, cast

import redis.asyncio as redis

from .base import BaseMemoryProvider, Message

logger = logging.getLogger(__name__)

@BaseMemoryProvider.register("redis")
class RedisMemoryProvider(BaseMemoryProvider):
    """Redis memory provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Redis memory provider.
        
        Args:
            config: Configuration dictionary containing:
                - host: Redis host
                - port: Redis port
                - db: Optional Redis database number
                - password: Optional Redis password
                - prefix: Optional key prefix (defaults to "pepperpy:messages:")
        """
        super().__init__(config)
        self.host = config["host"]
        self.port = config["port"]
        self.db = config.get("db", 0)
        self.password = config.get("password")
        self.prefix = config.get("prefix", "pepperpy:messages:")
        self.client: Optional[redis.Redis] = None
    
    async def initialize(self) -> bool:
        """Initialize the provider.
        
        Returns:
            True if initialization was successful.
            
        Raises:
            ValueError: If initialization fails.
        """
        if self.is_initialized:
            return True
            
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis provider: {str(e)}")
            await self.cleanup()
            raise ValueError(f"Redis initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
        if self.client:
            await self.client.close()
            self.client = None
        self.is_initialized = False
    
    def _get_key(self, timestamp: datetime) -> str:
        """Get Redis key for a message.
        
        Args:
            timestamp: Message timestamp.
            
        Returns:
            Redis key.
        """
        return f"{self.prefix}{timestamp.isoformat()}"
    
    async def add_message(self, message: Message) -> None:
        """Add a message to memory.
        
        Args:
            message: Message to add.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.client:
            raise ValueError("Redis client not initialized")
            
        try:
            key = self._get_key(message.timestamp)
            value = json.dumps(message.to_dict())
            await self.client.set(key, value)
            
            # Add to role index
            role_key = f"{self.prefix}role:{message.role}"
            await self.client.zadd(role_key, {key: message.timestamp.timestamp()})
            
        except Exception as e:
            logger.error(f"Failed to add message: {str(e)}")
            raise RuntimeError(f"Failed to add message: {str(e)}")
    
    async def get_messages(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        role: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get messages from memory.
        
        Args:
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            role: Optional role filter.
            limit: Optional limit on number of messages.
            
        Returns:
            List of messages.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.client:
            raise ValueError("Redis client not initialized")
            
        try:
            messages = []
            
            if role:
                # Get messages by role
                role_key = f"{self.prefix}role:{role}"
                min_score = start_time.timestamp() if start_time else "-inf"
                max_score = end_time.timestamp() if end_time else "+inf"
                keys = await self.client.zrangebyscore(
                    role_key,
                    min_score,
                    max_score,
                    start=0,
                    num=limit
                )
            else:
                # Get all message keys
                keys = await self.client.keys(f"{self.prefix}*")
                # Filter out role index keys
                keys = [k for k in keys if not k.startswith(f"{self.prefix}role:")]
                # Sort by timestamp
                keys.sort(reverse=True)
                if limit:
                    keys = keys[:limit]
            
            # Get message data
            for key in keys:
                if value := await self.client.get(key):
                    data = json.loads(value)
                    messages.append(Message.from_dict(data))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages: {str(e)}")
            raise RuntimeError(f"Failed to get messages: {str(e)}")
    
    async def clear_messages(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        role: Optional[str] = None
    ) -> None:
        """Clear messages from memory.
        
        Args:
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            role: Optional role filter.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.client:
            raise ValueError("Redis client not initialized")
            
        try:
            if role:
                # Delete messages by role
                role_key = f"{self.prefix}role:{role}"
                min_score = start_time.timestamp() if start_time else "-inf"
                max_score = end_time.timestamp() if end_time else "+inf"
                keys = await self.client.zrangebyscore(
                    role_key,
                    min_score,
                    max_score
                )
                if keys:
                    # Delete message data
                    await self.client.delete(*keys)
                    # Remove from role index
                    await self.client.zremrangebyscore(
                        role_key,
                        min_score,
                        max_score
                    )
            else:
                # Delete all messages
                keys = await self.client.keys(f"{self.prefix}*")
                if keys:
                    await self.client.delete(*keys)
            
        except Exception as e:
            logger.error(f"Failed to clear messages: {str(e)}")
            raise RuntimeError(f"Failed to clear messages: {str(e)}")
    
    async def search_messages(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Search messages in memory.
        
        Args:
            query: Search query.
            limit: Optional limit on number of results.
            
        Returns:
            List of matching messages.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.client:
            raise ValueError("Redis client not initialized")
            
        try:
            messages = []
            keys = await self.client.keys(f"{self.prefix}*")
            # Filter out role index keys
            keys = [k for k in keys if not k.startswith(f"{self.prefix}role:")]
            
            # Get message data and filter by content
            for key in keys:
                if value := await self.client.get(key):
                    data = json.loads(value)
                    if query.lower() in data["content"].lower():
                        messages.append(Message.from_dict(data))
                        if limit and len(messages) >= limit:
                            break
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to search messages: {str(e)}")
            raise RuntimeError(f"Failed to search messages: {str(e)}") 