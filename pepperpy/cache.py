"""Cache module for PepperPy.

This module was migrated from a subdirectory structure.
"""

from pepperpy.cache.base import CacheProvider
from pepperpy.cache.memory import MemoryCacheProvider

"""Cache provider interface."""

from abc import abstractmethod
from typing import Any, Dict, Optional, Set, TypeVar

from pepperpy.common import BaseProvider

T = TypeVar("T")


class CacheProvider(BaseProvider):
    """Base class for cache providers."""

    @abstractmethod
    def get(
        self,
        key: str,
        default: Optional[T] = None,
    ) -> Optional[T]:
        """Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Optional[T]: Cached value or default
        """
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Tags for invalidation
            metadata: Additional metadata
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        pass

    @abstractmethod
    def invalidate_tag(self, tag: str) -> None:
        """Invalidate all entries with tag.

        Args:
            tag: Tag to invalidate
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all entries."""
        pass
