"""Agent-specific cache system.

This module implements a cache system optimized for agent context,
focusing on:

- Context Cache
  - Interaction history
  - Agent state
  - Short-term memory
  - Temporary knowledge

- Specific Features
  - Relevance-based prioritization
  - Adaptive expiration
  - Selective compression
  - Optional persistence

This module is part of a unified caching architecture:
- This module (memory/cache.py): Agent-specific caching with context awareness
- pepperpy/caching/: Unified caching system with various backends

Both modules share core concepts but have specialized implementations.
This module now integrates with the unified caching system while
maintaining its agent-specific features.

The module provides:
- In-memory cache
- Redis cache
- Flexible serialization
- Eviction strategies
"""

import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union

# Import from the unified caching system

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with value and expiration."""

    value: T
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if the entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class CacheError(Exception):
    """Base exception for cache-related errors."""

    pass


class SerializationError(CacheError):
    """Error during value serialization/deserialization."""

    pass


class BackendError(CacheError):
    """Error in cache backend operation."""

    pass


class Serializer(ABC):
    """Base class for value serializers."""

    @abstractmethod
    def serialize(self, value: Any) -> bytes:
        """Serialize a value to bytes."""
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to a value."""
        pass


class PickleSerializer(Serializer):
    """Pickle-based serializer implementation."""

    def serialize(self, value: Any) -> bytes:
        """Serialize using pickle."""
        try:
            return pickle.dumps(value)
        except Exception as e:
            raise SerializationError(f"Failed to serialize value: {e}")

    def deserialize(self, data: bytes) -> Any:
        """Deserialize using pickle."""
        try:
            return pickle.loads(data)
        except Exception as e:
            raise SerializationError(f"Failed to deserialize value: {e}")


class CacheBackend(ABC, Generic[T]):
    """Base class for cache backends."""

    def __init__(self, serializer: Optional[Serializer] = None):
        self.serializer = serializer or PickleSerializer()

    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Retrieve a value from cache."""
        pass

    @abstractmethod
    def set(
        self, key: str, value: T, ttl: Optional[Union[int, timedelta]] = None
    ) -> None:
        """Store a value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all values from cache."""
        pass

    def _convert_ttl(self, ttl: Optional[Union[int, timedelta]]) -> Optional[datetime]:
        """Convert TTL to expiration datetime."""
        if ttl is None:
            return None
        if isinstance(ttl, int):
            ttl = timedelta(seconds=ttl)
        return datetime.now() + ttl


class MemoryCache(CacheBackend[T]):
    """In-memory cache implementation with TTL support."""

    def __init__(self, serializer: Optional[Serializer] = None):
        super().__init__(serializer)
        self._storage: Dict[str, CacheEntry[T]] = {}

    def get(self, key: str) -> Optional[T]:
        """Retrieve a value from memory cache."""
        entry = self._storage.get(key)
        if entry is None:
            return None

        if entry.is_expired():
            self.delete(key)
            return None

        return entry.value

    def set(
        self, key: str, value: T, ttl: Optional[Union[int, timedelta]] = None
    ) -> None:
        """Store a value in memory cache."""
        expires_at = self._convert_ttl(ttl)
        self._storage[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: str) -> bool:
        """Delete a value from memory cache."""
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all values from memory cache."""
        self._storage.clear()

    def cleanup_expired(self) -> None:
        """Remove all expired entries."""
        expired_keys = [
            key for key, entry in self._storage.items() if entry.is_expired()
        ]
        for key in expired_keys:
            self.delete(key)


class RedisCache(CacheBackend[T]):
    """Redis-based cache implementation."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        serializer: Optional[Serializer] = None,
    ):
        super().__init__(serializer)
        try:
            import redis

            self._client = redis.Redis(host=host, port=port, db=db)
        except ImportError:
            raise ImportError("Redis package is required for RedisCache")
        except Exception as e:
            raise BackendError(f"Failed to connect to Redis: {e}")

    def get(self, key: str) -> Optional[T]:
        """Retrieve a value from Redis cache."""
        try:
            value = self._client.get(key)
            if value is None:
                return None
            return self.serializer.deserialize(value)
        except SerializationError:
            raise
        except Exception as e:
            raise BackendError(f"Failed to get value from Redis: {e}")

    def set(
        self, key: str, value: T, ttl: Optional[Union[int, timedelta]] = None
    ) -> None:
        """Store a value in Redis cache."""
        try:
            serialized = self.serializer.serialize(value)
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            if ttl is not None:
                self._client.setex(key, ttl, serialized)
            else:
                self._client.set(key, serialized)
        except SerializationError:
            raise
        except Exception as e:
            raise BackendError(f"Failed to set value in Redis: {e}")

    def delete(self, key: str) -> bool:
        """Delete a value from Redis cache."""
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            raise BackendError(f"Failed to delete value from Redis: {e}")

    def clear(self) -> None:
        """Clear all values from Redis cache."""
        try:
            self._client.flushdb()
        except Exception as e:
            raise BackendError(f"Failed to clear Redis cache: {e}")


class CacheFactory:
    """Factory for creating cache backends."""

    _backends: Dict[str, Type[CacheBackend]] = {
        "memory": MemoryCache,
        "redis": RedisCache,
    }

    @classmethod
    def register_backend(cls, name: str, backend_class: Type[CacheBackend]) -> None:
        """Register a new cache backend."""
        if not issubclass(backend_class, CacheBackend):
            raise ValueError("Backend class must inherit from CacheBackend")
        cls._backends[name] = backend_class

    @classmethod
    def create(
        cls, backend_type: str, serializer: Optional[Serializer] = None, **kwargs
    ) -> CacheBackend:
        """Create a cache backend instance."""
        if backend_type not in cls._backends:
            raise ValueError(f"Unknown cache backend: {backend_type}")

        backend_class = cls._backends[backend_type]
        if serializer:
            kwargs["serializer"] = serializer

        try:
            return backend_class(**kwargs)
        except Exception as e:
            raise BackendError(f"Failed to create cache backend: {e}")
