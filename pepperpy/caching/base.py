"""Base classes and interfaces for the unified caching system.

This module provides the core abstractions for the caching system:
- CacheEntry: Container for cached values with metadata
- Serializer: Interface for value serialization/deserialization
- CachePolicy: Interface for cache eviction policies
- CacheBackend: Interface for storage backends
- Cache: High-level cache interface
"""

import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

T = TypeVar("T")
K = TypeVar("K", str, int, bytes)


class CacheError(Exception):
    """Base exception for cache-related errors."""

    pass


class SerializationError(CacheError):
    """Error during value serialization/deserialization."""

    pass


class BackendError(CacheError):
    """Error in cache backend operation."""

    pass


class PolicyError(CacheError):
    """Error in cache policy operation."""

    pass


@dataclass
class CacheEntry(Generic[T]):
    """Container for a cached value with metadata."""

    key: str
    value: T
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if the entry is expired.

        Returns:
            True if expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def touch(self) -> None:
        """Update last accessed time and increment access count."""
        self.last_accessed = datetime.now()
        self.access_count += 1


class Serializer(ABC):
    """Interface for value serializers."""

    @abstractmethod
    def serialize(self, value: Any) -> bytes:
        """Serialize a value to bytes.

        Args:
            value: Value to serialize

        Returns:
            Serialized bytes

        Raises:
            SerializationError: If serialization fails
        """
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to a value.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized value

        Raises:
            SerializationError: If deserialization fails
        """
        pass


class PickleSerializer(Serializer):
    """Pickle-based serializer implementation."""

    def serialize(self, value: Any) -> bytes:
        """Serialize using pickle.

        Args:
            value: Value to serialize

        Returns:
            Serialized bytes

        Raises:
            SerializationError: If serialization fails
        """
        try:
            return pickle.dumps(value)
        except Exception as e:
            raise SerializationError(f"Failed to serialize value: {e}") from e

    def deserialize(self, data: bytes) -> Any:
        """Deserialize using pickle.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized value

        Raises:
            SerializationError: If deserialization fails
        """
        try:
            return pickle.loads(data)
        except Exception as e:
            raise SerializationError(f"Failed to deserialize value: {e}") from e


class CachePolicyType(Enum):
    """Types of cache eviction policies."""

    LRU = "least_recently_used"
    LFU = "least_frequently_used"
    FIFO = "first_in_first_out"
    TTL = "time_to_live"
    RANDOM = "random"
    CUSTOM = "custom"


class CachePolicy(ABC):
    """Interface for cache eviction policies."""

    @property
    @abstractmethod
    def policy_type(self) -> CachePolicyType:
        """Get the policy type.

        Returns:
            Policy type enum value
        """
        pass

    @abstractmethod
    def select_entries_to_evict(
        self, entries: Dict[str, CacheEntry], count: int = 1
    ) -> List[str]:
        """Select entries to evict based on policy.

        Args:
            entries: Dictionary of cache entries
            count: Number of entries to select

        Returns:
            List of keys to evict

        Raises:
            PolicyError: If selection fails
        """
        pass


class CacheBackend(ABC, Generic[T]):
    """Interface for cache storage backends."""

    def __init__(self, serializer: Optional[Serializer] = None):
        """Initialize cache backend.

        Args:
            serializer: Optional serializer for values
        """
        self.serializer = serializer or PickleSerializer()

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise

        Raises:
            BackendError: If retrieval fails
        """
        pass

    @abstractmethod
    async def set(
        self, key: str, value: T, ttl: Optional[Union[int, timedelta]] = None
    ) -> None:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live (seconds or timedelta)

        Raises:
            BackendError: If storage fails
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found

        Raises:
            BackendError: If deletion fails
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from cache.

        Raises:
            BackendError: If clearing fails
        """
        pass

    @abstractmethod
    async def contains(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise

        Raises:
            BackendError: If check fails
        """
        pass

    def _convert_ttl(self, ttl: Optional[Union[int, timedelta]]) -> Optional[datetime]:
        """Convert TTL to expiration datetime.

        Args:
            ttl: Time-to-live (seconds or timedelta)

        Returns:
            Expiration datetime or None if no TTL
        """
        if ttl is None:
            return None
        if isinstance(ttl, int):
            ttl = timedelta(seconds=ttl)
        return datetime.now() + ttl


class Cache(Generic[T]):
    """High-level cache interface with policy support."""

    def __init__(
        self,
        backend: CacheBackend,
        policy: Optional[CachePolicy] = None,
        namespace: str = "",
    ):
        """Initialize cache.

        Args:
            backend: Cache storage backend
            policy: Optional eviction policy
            namespace: Optional namespace for keys
        """
        self.backend = backend
        self.policy = policy
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

    async def get(self, key: str) -> Optional[T]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        return await self.backend.get(self._make_key(key))

    async def set(
        self, key: str, value: T, ttl: Optional[Union[int, timedelta]] = None
    ) -> None:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live (seconds or timedelta)
        """
        await self.backend.set(self._make_key(key), value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        return await self.backend.delete(self._make_key(key))

    async def clear(self) -> None:
        """Clear all values from cache."""
        await self.backend.clear()

    async def contains(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        return await self.backend.contains(self._make_key(key))
