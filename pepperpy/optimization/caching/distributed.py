"""Cache distribuído para otimização de performance.

Implementa um sistema de cache distribuído usando Redis para otimização
de performance em requisições frequentes em ambientes distribuídos.
"""

from typing import Any, Dict, Optional, TypeVar

import redis

T = TypeVar("T")


class DistributedCache:
    """Distributed Redis-based cache implementation."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Initialize distributed cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            ttl: Default time to live in seconds
        """
        self._redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )
        self._ttl = ttl

    def get(self, key: str) -> Optional[T]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found
        """
        try:
            value = self._redis.get(key)
            return value if value is not None else None
        except redis.RedisError:
            return None

    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
        """
        try:
            if ttl is not None:
                self._redis.setex(key, ttl, value)
            elif self._ttl is not None:
                self._redis.setex(key, self._ttl, value)
            else:
                self._redis.set(key, value)
        except redis.RedisError:
            pass

    def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        try:
            self._redis.delete(key)
        except redis.RedisError:
            pass

    def clear(self) -> None:
        """Clear all cached values."""
        try:
            self._redis.flushdb()
        except redis.RedisError:
            pass

    def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            return bool(self._redis.exists(key))
        except redis.RedisError:
            return False

    def ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds or None if no TTL
        """
        try:
            ttl = self._redis.ttl(key)
            return ttl if ttl > 0 else None
        except redis.RedisError:
            return None

    def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching pattern.

        Args:
            pattern: Key pattern to match

        Returns:
            List of matching keys
        """
        try:
            return self._redis.keys(pattern)
        except redis.RedisError:
            return []

    @property
    def info(self) -> Dict[str, Any]:
        """Get Redis server info.

        Returns:
            Server information
        """
        try:
            return self._redis.info()
        except redis.RedisError:
            return {}
