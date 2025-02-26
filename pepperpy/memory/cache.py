"""Cache system implementation for the Pepperpy framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T")


class CacheBackend(ABC):
    """Base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
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


class MemoryCache(CacheBackend):
    """In-memory cache implementation."""

    def __init__(self):
        self._storage: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory cache."""
        return self._storage.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in memory cache."""
        # TTL não implementado para cache em memória simples
        self._storage[key] = value

    def delete(self, key: str) -> bool:
        """Delete a value from memory cache."""
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all values from memory cache."""
        self._storage.clear()


class RedisCache(CacheBackend):
    """Redis-based cache implementation."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            import redis

            self._client = redis.Redis(host=host, port=port, db=db)
        except ImportError:
            raise ImportError("Redis package is required for RedisCache")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from Redis cache."""
        value = self._client.get(key)
        if value is not None:
            import pickle

            return pickle.loads(value)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in Redis cache."""
        import pickle

        serialized = pickle.dumps(value)
        if ttl is not None:
            self._client.setex(key, ttl, serialized)
        else:
            self._client.set(key, serialized)

    def delete(self, key: str) -> bool:
        """Delete a value from Redis cache."""
        return bool(self._client.delete(key))

    def clear(self) -> None:
        """Clear all values from Redis cache."""
        self._client.flushdb()


class CacheFactory:
    """Factory for creating cache backends."""

    _backends: Dict[str, Type[CacheBackend]] = {
        "memory": MemoryCache,
        "redis": RedisCache,
    }

    @classmethod
    def register_backend(cls, name: str, backend_class: Type[CacheBackend]) -> None:
        """Register a new cache backend."""
        cls._backends[name] = backend_class

    @classmethod
    def create(cls, backend_type: str, **kwargs) -> CacheBackend:
        """Create a cache backend instance."""
        if backend_type not in cls._backends:
            raise ValueError(f"Unknown cache backend: {backend_type}")

        return cls._backends[backend_type](**kwargs)
