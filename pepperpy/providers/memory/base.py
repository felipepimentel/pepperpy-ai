"""Base memory provider interface.

This module defines the base interface for memory providers.
It includes:
- Base memory provider interface
- Memory configuration
- Common memory types
"""

from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from pepperpy.providers.base import BaseProvider, ProviderConfig

# Type variable for memory values
T = TypeVar("T")


class MemoryConfig(ProviderConfig):
    """Memory provider configuration.

    Attributes:
        ttl: Time-to-live in seconds (0 for no expiration)
        max_size: Maximum number of items (0 for unlimited)
        eviction_policy: Cache eviction policy
    """

    ttl: int = 0
    max_size: int = 0
    eviction_policy: str = "lru"


class MemoryItem(BaseModel, Generic[T]):
    """Memory item model.

    Attributes:
        key: Item key
        value: Item value
        created_at: Creation timestamp
        expires_at: Expiration timestamp
        metadata: Additional metadata
    """

    key: str
    value: T
    created_at: float
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseMemoryProvider(BaseProvider[MemoryItem[T]]):
    """Base class for memory providers.

    This class defines the interface that all memory providers must implement.
    """

    def __init__(self, config: MemoryConfig) -> None:
        """Initialize memory provider.

        Args:
            config: Memory configuration
        """
        super().__init__(config)
        self.ttl = config.ttl
        self.max_size = config.max_size
        self.eviction_policy = config.eviction_policy

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get value by key.

        Args:
            key: Item key

        Returns:
            Item value or None if not found

        Raises:
            ProviderError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple values by keys.

        Args:
            keys: Item keys

        Returns:
            Dictionary of found items

        Raises:
            ProviderError: If retrieval fails
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
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
        pass

    @abstractmethod
    async def set_many(
        self,
        items: Dict[str, T],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem[T]]:
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
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value by key.

        Args:
            key: Item key

        Returns:
            True if item was deleted

        Raises:
            ProviderError: If deletion fails
        """
        pass

    @abstractmethod
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple values.

        Args:
            keys: Item keys

        Returns:
            Number of deleted items

        Raises:
            ProviderError: If deletion fails
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Item key

        Returns:
            True if key exists

        Raises:
            ProviderError: If check fails
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all items.

        Raises:
            ProviderError: If clearing fails
        """
        pass

    @abstractmethod
    async def get_metadata(self, key: str) -> Optional[MemoryItem[T]]:
        """Get item metadata.

        Args:
            key: Item key

        Returns:
            Memory item or None if not found

        Raises:
            ProviderError: If metadata retrieval fails
        """
        pass

    @abstractmethod
    async def update_metadata(
        self, key: str, metadata: Dict[str, Any]
    ) -> Optional[MemoryItem[T]]:
        """Update item metadata.

        Args:
            key: Item key
            metadata: New metadata

        Returns:
            Updated item or None if not found

        Raises:
            ProviderError: If update fails
        """
        pass

    @abstractmethod
    async def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Optional glob pattern

        Returns:
            List of matching keys

        Raises:
            ProviderError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key.

        Args:
            key: Item key

        Returns:
            Remaining TTL in seconds or None if no TTL

        Raises:
            ProviderError: If TTL retrieval fails
        """
        pass

    @abstractmethod
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
        pass

    async def validate(self) -> None:
        """Validate provider configuration and state.

        Raises:
            ConfigurationError: If validation fails
        """
        if self.ttl < 0:
            raise ValueError("TTL must be non-negative")
        if self.max_size < 0:
            raise ValueError("Max size must be non-negative")
        if self.eviction_policy not in {"lru", "lfu", "fifo"}:
            raise ValueError("Invalid eviction policy")
