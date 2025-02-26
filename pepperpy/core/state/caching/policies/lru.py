"""LRU (Least Recently Used) cache policy implementation."""

import time
from typing import Any, Generic

from pepperpy.caching.errors import CachePolicyError
from pepperpy.caching.policies.base import CachePolicy
from pepperpy.caching.types import CacheKey, CacheMetadata, CacheValueType


class LRUPolicy(CachePolicy[CacheValueType], Generic[CacheValueType]):
    """LRU (Least Recently Used) cache policy.

    This policy evicts the least recently used items when the cache reaches
    its maximum capacity.

    Attributes:
        max_size: Maximum number of items to store
        update_access_on_get: Whether to update access time on get operations
    """

    def __init__(
        self,
        max_size: int = 1000,
        update_access_on_get: bool = True,
    ) -> None:
        """Initialize the LRU policy.

        Args:
            max_size: Maximum number of items to store
            update_access_on_get: Whether to update access time on get operations

        Raises:
            CachePolicyError: If max_size is invalid
        """
        if max_size <= 0:
            raise CachePolicyError("max_size must be positive")

        self.max_size = max_size
        self.update_access_on_get = update_access_on_get
        self._access_times: dict[CacheKey, float] = {}

    def should_cache(
        self,
        key: CacheKey,
        value: CacheValueType,
        metadata: CacheMetadata | None = None,
    ) -> bool:
        """Determine if a value should be cached.

        The value will be cached if:
        1. The cache has not reached max capacity, or
        2. The key already exists in the cache

        Args:
            key: The cache key
            value: The value to potentially cache
            metadata: Optional metadata about the value

        Returns:
            True if the value should be cached
        """
        return len(self._access_times) < self.max_size or key in self._access_times

    def should_evict(
        self,
        key: CacheKey,
        metadata: CacheMetadata | None = None,
    ) -> bool:
        """Determine if a value should be evicted.

        A value is evicted if it has the oldest access time.

        Args:
            key: The cache key
            metadata: Optional metadata about the value

        Returns:
            True if the value should be evicted
        """
        if not self._access_times:
            return False

        oldest_key = min(
            self._access_times.items(),
            key=lambda x: x[1],
        )[0]
        return key == oldest_key

    def update_access(self, key: CacheKey) -> None:
        """Update the access time for a key.

        Args:
            key: The cache key to update
        """
        self._access_times[key] = time.time()

    def remove_access(self, key: CacheKey) -> None:
        """Remove access time tracking for a key.

        Args:
            key: The cache key to remove
        """
        self._access_times.pop(key, None)

    def get_config(self) -> dict[str, Any]:
        """Get the policy configuration.

        Returns:
            Dictionary containing:
            - max_size: Maximum number of items to store
            - update_access_on_get: Whether to update access time on get operations
        """
        return {
            "max_size": self.max_size,
            "update_access_on_get": self.update_access_on_get,
        }

    def update_config(self, config: dict[str, Any]) -> None:
        """Update the policy configuration.

        Args:
            config: New configuration values

        Raises:
            CachePolicyError: If the configuration is invalid
        """
        if "max_size" in config:
            max_size = config["max_size"]
            if not isinstance(max_size, int) or max_size <= 0:
                raise CachePolicyError("max_size must be a positive integer")
            self.max_size = max_size

        if "update_access_on_get" in config:
            update_access_on_get = config["update_access_on_get"]
            if not isinstance(update_access_on_get, bool):
                raise CachePolicyError("update_access_on_get must be a boolean")
            self.update_access_on_get = update_access_on_get
