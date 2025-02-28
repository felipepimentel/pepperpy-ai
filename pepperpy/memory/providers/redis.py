"""Redis memory provider module.

This module implements the Redis provider for memory functionality.
"""

import json
import os
import time
from typing import Any, TypeVar, cast

import redis.asyncio as redis
from structlog import get_logger

from pepperpy.core.errors import ConfigurationError, ProviderError
from pepperpy.memory.providers.base import MemoryItem, MemoryProvider
from pepperpy.core.providers.unified import ProviderConfig

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

    url: str | None = None
    password: str | None = None
    db: int = 0
    encoding: str = "utf-8"


class RedisMemoryProvider(MemoryProvider[T]):
    """Redis memory provider implementation."""

    def __init__(self, config: RedisConfig) -> None:
        """Initialize Redis provider.

        Args:
            config: Redis configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__(config)
        self.url = config.url
        self.password = config.password
        self.db = config.db
        self.encoding = config.encoding
        self._client: redis.Redis | None = None

    async def initialize(self) -> None:
        """Initialize the provider.

        This method sets up the Redis client.

        Raises:
            ConfigurationError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Get Redis URL from environment or config
            url = self.url or os.getenv("REDIS_URL")
            if not url:
                raise ConfigurationError("Redis URL not provided")

            # Initialize client
            self._client = redis.from_url(
                url,
                password=self.password,
                db=self.db,
                encoding=self.encoding,
                decode_responses=True,
            )

            # Test connection
            await self._client.ping()

            self._initialized = True
            logger.info("Redis provider initialized", extra={"url": url})

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Redis provider: {e}")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            await self._client.close()
        self._initialized = False
        logger.info("Redis provider cleaned up")

    async def get(self, key: str) -> T | None:
        """Get value by key.

        Args:
            key: Item key

        Returns:
            Item value or None if not found

        Raises:
            ProviderError: If retrieval fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Get value from Redis
            value = await self._client.get(key)
            if value is None:
                return None

            # Parse JSON value
            return cast(T, json.loads(value))

        except Exception as e:
            raise ProviderError(f"Failed to get value: {e}")

    async def get_many(self, keys: list[str]) -> dict[str, T]:
        """Get multiple values by keys.

        Args:
            keys: Item keys

        Returns:
            Dictionary of found items

        Raises:
            ProviderError: If retrieval fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Get values from Redis
            values = await self._client.mget(keys)
            result: dict[str, T] = {}

            # Parse JSON values
            for key, value in zip(keys, values, strict=False):
                if value is not None:
                    result[key] = cast(T, json.loads(value))

            return result

        except Exception as e:
            raise ProviderError(f"Failed to get values: {e}")

    async def set(
        self,
        key: str,
        value: T,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryItem[T]:
        """Set value by key.

        Args:
            key: Item key
            value: Item value
            ttl: Optional TTL override
            metadata: Optional metadata

        Returns:
            Created memory item

        Raises:
            ProviderError: If storage fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Create memory item
            now = time.time()
            item = MemoryItem(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + (ttl or self.ttl) if ttl or self.ttl else None,
                metadata=metadata or {},
            )

            # Store value and metadata
            pipe = self._client.pipeline()
            pipe.set(key, json.dumps(value))
            if ttl or self.ttl:
                pipe.expire(key, ttl or self.ttl)
            if metadata:
                pipe.hset(f"{key}:metadata", mapping=metadata)
            await pipe.execute()

            return item

        except Exception as e:
            raise ProviderError(f"Failed to set value: {e}")

    async def set_many(
        self,
        items: dict[str, T],
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[MemoryItem[T]]:
        """Set multiple values.

        Args:
            items: Dictionary of items to store
            ttl: Optional TTL override
            metadata: Optional metadata

        Returns:
            List of created items

        Raises:
            ProviderError: If storage fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Create memory items
            now = time.time()
            memory_items = []
            pipe = self._client.pipeline()

            # Queue operations
            for key, value in items.items():
                item = MemoryItem(
                    key=key,
                    value=value,
                    created_at=now,
                    expires_at=now + (ttl or self.ttl) if ttl or self.ttl else None,
                    metadata=metadata or {},
                )
                memory_items.append(item)

                # Queue value storage
                pipe.set(key, json.dumps(value))
                if ttl or self.ttl:
                    pipe.expire(key, ttl or self.ttl)
                if metadata:
                    pipe.hset(f"{key}:metadata", mapping=metadata)

            # Execute pipeline
            await pipe.execute()
            return memory_items

        except Exception as e:
            raise ProviderError(f"Failed to set values: {e}")

    async def delete(self, key: str) -> bool:
        """Delete value by key.

        Args:
            key: Item key

        Returns:
            True if item was deleted

        Raises:
            ProviderError: If deletion fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Delete value and metadata
            pipe = self._client.pipeline()
            pipe.delete(key)
            pipe.delete(f"{key}:metadata")
            results = await pipe.execute()
            return bool(results[0])

        except Exception as e:
            raise ProviderError(f"Failed to delete key: {e}")

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple values.

        Args:
            keys: Item keys

        Returns:
            Number of deleted items

        Raises:
            ProviderError: If deletion fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Delete values and metadata
            pipe = self._client.pipeline()
            for key in keys:
                pipe.delete(key)
                pipe.delete(f"{key}:metadata")
            results = await pipe.execute()
            return sum(1 for r in results[::2] if r)

        except Exception as e:
            raise ProviderError(f"Failed to delete keys: {e}")

    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Item key

        Returns:
            True if key exists

        Raises:
            ProviderError: If check fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            return bool(await self._client.exists(key))
        except Exception as e:
            raise ProviderError(f"Failed to check key: {e}")

    async def clear(self) -> None:
        """Clear all items.

        Raises:
            ProviderError: If clearing fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            await self._client.flushdb()
        except Exception as e:
            raise ProviderError(f"Failed to clear items: {e}")

    async def get_metadata(self, key: str) -> MemoryItem[T] | None:
        """Get item metadata.

        Args:
            key: Item key

        Returns:
            Memory item or None if not found

        Raises:
            ProviderError: If metadata retrieval fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Get value and metadata
            pipe = self._client.pipeline()
            pipe.get(key)
            pipe.hgetall(f"{key}:metadata")
            results = await pipe.execute()
            value, metadata = results

            if value is None:
                return None

            # Create memory item
            return MemoryItem(
                key=key,
                value=cast(T, json.loads(value)),
                created_at=time.time(),  # Redis doesn't store creation time
                metadata=metadata or {},
            )

        except Exception as e:
            raise ProviderError(f"Failed to get metadata: {e}")

    async def update_metadata(
        self, key: str, metadata: dict[str, Any]
    ) -> MemoryItem[T] | None:
        """Update item metadata.

        Args:
            key: Item key
            metadata: New metadata

        Returns:
            Updated item or None if not found

        Raises:
            ProviderError: If update fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Check if key exists
            if not await self.exists(key):
                return None

            # Update metadata
            await self._client.hset(f"{key}:metadata", mapping=metadata)

            # Return updated item
            return await self.get_metadata(key)

        except Exception as e:
            raise ProviderError(f"Failed to update metadata: {e}")

    async def get_keys(self, pattern: str | None = None) -> list[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Optional glob pattern

        Returns:
            List of matching keys

        Raises:
            ProviderError: If retrieval fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            # Get keys matching pattern
            keys = await self._client.keys(pattern or "*")
            return [k for k in keys if not k.endswith(":metadata")]
        except Exception as e:
            raise ProviderError(f"Failed to get keys: {e}")

    async def get_ttl(self, key: str) -> int | None:
        """Get remaining TTL for key.

        Args:
            key: Item key

        Returns:
            Remaining TTL in seconds or None if no TTL

        Raises:
            ProviderError: If TTL retrieval fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            ttl = await self._client.ttl(key)
            return None if ttl == -1 else ttl
        except Exception as e:
            raise ProviderError(f"Failed to get TTL: {e}")

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Set TTL for key.

        Args:
            key: Item key
            ttl: New TTL in seconds

        Returns:
            True if TTL was set

        Raises:
            ProviderError: If TTL update fails
        """
        if not self._initialized or not self._client:
            raise ProviderError("Provider not initialized")

        try:
            return bool(await self._client.expire(key, ttl))
        except Exception as e:
            raise ProviderError(f"Failed to set TTL: {e}")
