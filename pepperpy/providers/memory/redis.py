"""Redis memory provider module.

This module implements the Redis provider for memory functionality.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, TypeVar

import redis.asyncio as redis
from structlog import get_logger

from pepperpy.core.common.providers.unified import ProviderConfig
from pepperpy.core.errors import ConfigurationError, ProviderError
from pepperpy.providers.memory.base import MemoryItem, MemoryProvider

T = TypeVar("T")
logger = get_logger(__name__)


class RedisConfig(ProviderConfig):
    """Redis provider configuration.

    Args:
        url: Redis connection URL
        password: Redis password
        db: Redis database number
        encoding: Character encoding
    """

    url: Optional[str] = None
    password: Optional[str] = None
    db: int = 0
    encoding: str = "utf-8"


class RedisMemoryProvider(MemoryProvider[T]):
    """Provider implementation for Redis-based memory storage."""

    def __init__(self, config: RedisConfig) -> None:
        """Initialize Redis provider.

        Args:
            config: Redis configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__(config)
        self.config = config
        self.client = None
        self.prefix = "memory:"

        # Validate configuration
        if not config.url and not os.environ.get("REDIS_URL"):
            raise ConfigurationError("Redis URL must be provided")

    async def initialize(self) -> None:
        """Initialize Redis client.

        Raises:
            ProviderError: If initialization fails
        """
        try:
            url = self.config.url or os.environ.get("REDIS_URL")
            self.client = redis.from_url(
                url,
                password=self.config.password,
                db=self.config.db,
                encoding=self.config.encoding,
                decode_responses=True,
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis provider initialized", url=url)
        except Exception as e:
            raise ProviderError(f"Failed to initialize Redis client: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.close()
            logger.info("Redis provider cleaned up")

    async def get(self, key: str) -> Optional[T]:
        """Get value by key.

        Args:
            key: Key to get

        Returns:
            Value associated with key or None if not found

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            full_key = f"{self.prefix}{key}"
            data = await self.client.get(full_key)
            if not data:
                return None

            # Parse JSON data
            item_data = json.loads(data)
            item = MemoryItem[T](**item_data)

            # Check if expired
            if item.expires_at and item.expires_at < time.time():
                await self.delete(key)
                return None

            return item.value
        except Exception as e:
            raise ProviderError(f"Failed to get value: {e}")

    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple values by keys.

        Args:
            keys: Keys to get

        Returns:
            Dictionary mapping keys to values

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        result: Dict[str, T] = {}
        if not keys:
            return result

        try:
            # Prepare full keys
            full_keys = [f"{self.prefix}{key}" for key in keys]

            # Get values in a pipeline
            pipe = self.client.pipeline()
            for key in full_keys:
                pipe.get(key)
            values = await pipe.execute()

            # Process results
            for i, data in enumerate(values):
                if not data:
                    continue

                # Parse JSON data
                item_data = json.loads(data)
                item = MemoryItem[T](**item_data)

                # Check if expired
                if item.expires_at and item.expires_at < time.time():
                    await self.delete(keys[i])
                    continue

                result[keys[i]] = item.value

            return result
        except Exception as e:
            raise ProviderError(f"Failed to get multiple values: {e}")

    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem[T]:
        """Set value by key.

        Args:
            key: Key to set
            value: Value to set
            ttl: Time to live in seconds
            metadata: Optional metadata

        Returns:
            Memory item

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            # Create memory item
            now = time.time()
            expires_at = now + ttl if ttl is not None else None
            item = MemoryItem[T](
                value=value,
                created_at=now,
                expires_at=expires_at,
                metadata=metadata or {},
            )

            # Serialize to JSON
            data = item.model_dump_json()

            # Store in Redis
            full_key = f"{self.prefix}{key}"
            if ttl is not None:
                await self.client.setex(full_key, ttl, data)
            else:
                await self.client.set(full_key, data)

            return item
        except Exception as e:
            raise ProviderError(f"Failed to set value: {e}")

    async def set_many(
        self,
        items: Dict[str, T],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem[T]]:
        """Set multiple values.

        Args:
            items: Dictionary mapping keys to values
            ttl: Time to live in seconds
            metadata: Optional metadata

        Returns:
            List of memory items

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        result: List[MemoryItem[T]] = []
        if not items:
            return result

        try:
            # Create memory items
            now = time.time()
            expires_at = now + ttl if ttl is not None else None
            memory_items = {}

            for key, value in items.items():
                item = MemoryItem[T](
                    value=value,
                    created_at=now,
                    expires_at=expires_at,
                    metadata=metadata or {},
                )
                memory_items[key] = item
                result.append(item)

            # Store in Redis pipeline
            pipe = self.client.pipeline()
            for key, item in memory_items.items():
                full_key = f"{self.prefix}{key}"
                data = item.model_dump_json()
                if ttl is not None:
                    pipe.setex(full_key, ttl, data)
                else:
                    pipe.set(full_key, data)
            await pipe.execute()

            return result
        except Exception as e:
            raise ProviderError(f"Failed to set multiple values: {e}")

    async def delete(self, key: str) -> bool:
        """Delete value by key.

        Args:
            key: Key to delete

        Returns:
            True if key was deleted, False otherwise

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            full_key = f"{self.prefix}{key}"
            result = await self.client.delete(full_key)
            return result > 0
        except Exception as e:
            raise ProviderError(f"Failed to delete value: {e}")

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple values.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        if not keys:
            return 0

        try:
            # Prepare full keys
            full_keys = [f"{self.prefix}{key}" for key in keys]

            # Delete in a single operation
            result = await self.client.delete(*full_keys)
            return result
        except Exception as e:
            raise ProviderError(f"Failed to delete multiple values: {e}")

    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            full_key = f"{self.prefix}{key}"
            result = await self.client.exists(full_key)
            return result > 0
        except Exception as e:
            raise ProviderError(f"Failed to check key existence: {e}")

    async def clear(self) -> None:
        """Clear all values.

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            # Get all keys with prefix
            keys = await self.get_keys()
            if keys:
                # Delete all keys
                full_keys = [f"{self.prefix}{key}" for key in keys]
                await self.client.delete(*full_keys)
        except Exception as e:
            raise ProviderError(f"Failed to clear values: {e}")

    async def get_metadata(self, key: str) -> Optional[MemoryItem[T]]:
        """Get item metadata.

        Args:
            key: Key to get metadata for

        Returns:
            Memory item or None if key does not exist

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            full_key = f"{self.prefix}{key}"
            data = await self.client.get(full_key)
            if not data:
                return None

            # Parse JSON data
            item_data = json.loads(data)
            item = MemoryItem[T](**item_data)

            # Check if expired
            if item.expires_at and item.expires_at < time.time():
                await self.delete(key)
                return None

            return item
        except Exception as e:
            raise ProviderError(f"Failed to get metadata: {e}")

    async def update_metadata(
        self, key: str, metadata: Dict[str, Any]
    ) -> Optional[MemoryItem[T]]:
        """Update item metadata.

        Args:
            key: Key to update metadata for
            metadata: New metadata

        Returns:
            Updated memory item or None if key does not exist

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            # Get current item
            item = await self.get_metadata(key)
            if not item:
                return None

            # Update metadata
            item.metadata.update(metadata)

            # Store updated item
            full_key = f"{self.prefix}{key}"
            data = item.model_dump_json()

            # Calculate remaining TTL
            ttl = None
            if item.expires_at:
                ttl = int(item.expires_at - time.time())
                if ttl <= 0:
                    await self.delete(key)
                    return None

            # Store in Redis
            if ttl is not None:
                await self.client.setex(full_key, ttl, data)
            else:
                await self.client.set(full_key, data)

            return item
        except Exception as e:
            raise ProviderError(f"Failed to update metadata: {e}")

    async def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Pattern to match keys against

        Returns:
            List of matching keys

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            # Prepare pattern
            full_pattern = f"{self.prefix}{pattern or '*'}"
            keys = await self.client.keys(full_pattern)

            # Remove prefix from keys
            prefix_len = len(self.prefix)
            return [key[prefix_len:] for key in keys]
        except Exception as e:
            raise ProviderError(f"Failed to get keys: {e}")

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key.

        Args:
            key: Key to get TTL for

        Returns:
            Remaining TTL in seconds or None if key does not exist or has no TTL

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            full_key = f"{self.prefix}{key}"
            ttl = await self.client.ttl(full_key)
            if ttl < 0:
                return None
            return ttl
        except Exception as e:
            raise ProviderError(f"Failed to get TTL: {e}")

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Set TTL for key.

        Args:
            key: Key to set TTL for
            ttl: TTL in seconds

        Returns:
            True if TTL was set, False otherwise

        Raises:
            ProviderError: If operation fails
        """
        if not self.client:
            raise ProviderError("Redis client not initialized")

        try:
            full_key = f"{self.prefix}{key}"
            result = await self.client.expire(full_key, ttl)
            return result > 0
        except Exception as e:
            raise ProviderError(f"Failed to set TTL: {e}")
