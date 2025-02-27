"""Distributed cache implementations for the unified caching system.

This module provides distributed cache implementations with:
- Redis backend support
- Cluster configuration
- Pub/sub capabilities
- Serialization options
"""

import json
from datetime import timedelta
from typing import Any, Optional, Union

from .base import BackendError, CacheBackend, Serializer, T


class DistributedCache(CacheBackend[T]):
    """Base class for distributed cache implementations."""

    def __init__(
        self,
        serializer: Optional[Serializer] = None,
        namespace: str = "",
    ):
        """Initialize distributed cache.

        Args:
            serializer: Optional serializer for values
            namespace: Optional namespace for keys
        """
        super().__init__(serializer)
        self.namespace = namespace

    def _make_key(self, key: str) -> str:
        """Create namespaced key.

        Args:
            key: Original key

        Returns:
            Namespaced key
        """
        if not self.namespace:
            return key
        return f"{self.namespace}:{key}"


class RedisCache(DistributedCache[T]):
    """Redis-based distributed cache implementation."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        serializer: Optional[Serializer] = None,
        namespace: str = "",
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
    ):
        """Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional Redis password
            serializer: Optional serializer for values
            namespace: Optional namespace for keys
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
            retry_on_timeout: Whether to retry on timeout

        Raises:
            ImportError: If Redis package is not installed
            BackendError: If connection fails
        """
        super().__init__(serializer, namespace)

        try:
            import redis

            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                retry_on_timeout=retry_on_timeout,
            )

            # Test connection
            self._client.ping()

        except ImportError:
            raise ImportError(
                "Redis package is required for RedisCache. "
                "Install it with: pip install redis"
            )
        except Exception as e:
            raise BackendError(f"Failed to connect to Redis: {e}")

    async def get(self, key: str) -> Optional[T]:
        """Get a value from Redis cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise

        Raises:
            BackendError: If retrieval fails
        """
        try:
            namespaced_key = self._make_key(key)
            value = self._client.get(namespaced_key)

            if value is None:
                return None

            return self.serializer.deserialize(value)

        except Exception as e:
            raise BackendError(f"Failed to get value from Redis: {e}")

    async def set(
        self, key: str, value: T, ttl: Optional[Union[int, timedelta]] = None
    ) -> None:
        """Set a value in Redis cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live (seconds or timedelta)

        Raises:
            BackendError: If storage fails
        """
        try:
            namespaced_key = self._make_key(key)
            serialized = self.serializer.serialize(value)

            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            if ttl is not None:
                self._client.setex(namespaced_key, ttl, serialized)
            else:
                self._client.set(namespaced_key, serialized)

        except Exception as e:
            raise BackendError(f"Failed to set value in Redis: {e}")

    async def delete(self, key: str) -> bool:
        """Delete a value from Redis cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found

        Raises:
            BackendError: If deletion fails
        """
        try:
            namespaced_key = self._make_key(key)
            return bool(self._client.delete(namespaced_key))

        except Exception as e:
            raise BackendError(f"Failed to delete value from Redis: {e}")

    async def clear(self) -> None:
        """Clear all values from Redis cache with the current namespace.

        Raises:
            BackendError: If clearing fails
        """
        try:
            if self.namespace:
                # Only delete keys with the current namespace
                pattern = f"{self.namespace}:*"
                keys = self._client.keys(pattern)
                if keys:
                    self._client.delete(*keys)
            else:
                # Clear the entire database
                self._client.flushdb()

        except Exception as e:
            raise BackendError(f"Failed to clear Redis cache: {e}")

    async def contains(self, key: str) -> bool:
        """Check if key exists in Redis cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise

        Raises:
            BackendError: If check fails
        """
        try:
            namespaced_key = self._make_key(key)
            return bool(self._client.exists(namespaced_key))

        except Exception as e:
            raise BackendError(f"Failed to check key existence in Redis: {e}")

    async def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a Redis channel.

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of clients that received the message

        Raises:
            BackendError: If publishing fails
        """
        try:
            # Serialize message to JSON
            if isinstance(message, (str, int, float, bool, type(None))):
                json_message = json.dumps(message)
            else:
                # For complex objects, use the serializer
                serialized = self.serializer.serialize(message)
                json_message = json.dumps({
                    "_serialized": True,
                    "data": serialized.hex(),
                })

            # Publish to channel
            return self._client.publish(channel, json_message)

        except Exception as e:
            raise BackendError(f"Failed to publish message to Redis: {e}")

    def subscribe(self, *channels: str):
        """Subscribe to Redis channels.

        Args:
            *channels: Channel names

        Returns:
            Redis pubsub object

        Raises:
            BackendError: If subscription fails
        """
        try:
            pubsub = self._client.pubsub()
            pubsub.subscribe(*channels)
            return pubsub

        except Exception as e:
            raise BackendError(f"Failed to subscribe to Redis channels: {e}")

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a value in Redis.

        Args:
            key: Cache key
            amount: Amount to increment

        Returns:
            New value

        Raises:
            BackendError: If increment fails
        """
        try:
            namespaced_key = self._make_key(key)
            return self._client.incrby(namespaced_key, amount)

        except Exception as e:
            raise BackendError(f"Failed to increment value in Redis: {e}")

    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration for a key.

        Args:
            key: Cache key
            ttl: Time-to-live (seconds or timedelta)

        Returns:
            True if expiration was set, False if key doesn't exist

        Raises:
            BackendError: If setting expiration fails
        """
        try:
            namespaced_key = self._make_key(key)

            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            return bool(self._client.expire(namespaced_key, ttl))

        except Exception as e:
            raise BackendError(f"Failed to set expiration in Redis: {e}")

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining time-to-live for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, None if key doesn't exist or has no expiration

        Raises:
            BackendError: If getting TTL fails
        """
        try:
            namespaced_key = self._make_key(key)
            ttl = self._client.ttl(namespaced_key)

            # Redis returns -1 if key exists but has no expiration
            # Redis returns -2 if key doesn't exist
            if ttl < 0:
                return None

            return ttl

        except Exception as e:
            raise BackendError(f"Failed to get TTL from Redis: {e}")
