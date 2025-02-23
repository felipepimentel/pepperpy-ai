"""Resource cache system.

This module provides caching functionality for resources.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from pepperpy.resources.base import BaseResource

# Configure logging
logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry class.

    This class represents a cached resource entry.
    """

    def __init__(
        self,
        resource: BaseResource,
        ttl: Optional[int] = None,
    ) -> None:
        """Initialize cache entry.

        Args:
            resource: Cached resource
            ttl: Time to live in seconds
        """
        self.resource = resource
        self.created_at = datetime.utcnow()
        self.accessed_at = self.created_at
        self.expires_at = (
            self.created_at + timedelta(seconds=ttl) if ttl is not None else None
        )

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return self.expires_at is not None and datetime.utcnow() > self.expires_at

    def touch(self) -> None:
        """Update last access time."""
        self.accessed_at = datetime.utcnow()


class ResourceCache:
    """Resource cache implementation.

    This class provides caching functionality for resources.
    """

    def __init__(
        self,
        max_size: Optional[int] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        """Initialize cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default time to live in seconds
        """
        self._entries: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    @property
    def size(self) -> int:
        """Get cache size."""
        return len(self._entries)

    async def get(self, resource_id: str) -> Optional[BaseResource]:
        """Get resource from cache.

        Args:
            resource_id: Resource ID

        Returns:
            Optional[BaseResource]: Cached resource if found and not expired
        """
        async with self._lock:
            entry = self._entries.get(resource_id)
            if entry is None:
                return None

            if entry.is_expired:
                await self.invalidate(resource_id)
                return None

            entry.touch()
            return entry.resource

    async def set(
        self,
        resource: BaseResource,
        ttl: Optional[int] = None,
    ) -> None:
        """Set resource in cache.

        Args:
            resource: Resource to cache
            ttl: Time to live in seconds (overrides default)

        Raises:
            ResourceError: If cache is full
        """
        async with self._lock:
            # Check if cache is full
            if (
                self._max_size is not None
                and len(self._entries) >= self._max_size
                and resource.id not in self._entries
            ):
                # Try to remove expired entries first
                await self._cleanup_expired()

                # If still full, remove least recently used entry
                if len(self._entries) >= self._max_size:
                    await self._remove_lru()

            # Create new entry
            self._entries[resource.id] = CacheEntry(
                resource,
                ttl=ttl if ttl is not None else self._default_ttl,
            )

    async def invalidate(self, resource_id: str) -> None:
        """Invalidate cached resource.

        Args:
            resource_id: Resource ID
        """
        async with self._lock:
            if resource_id in self._entries:
                del self._entries[resource_id]

    async def clear(self) -> None:
        """Clear all cached resources."""
        async with self._lock:
            self._entries.clear()

    async def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired = [
            resource_id
            for resource_id, entry in self._entries.items()
            if entry.is_expired
        ]
        for resource_id in expired:
            await self.invalidate(resource_id)

    async def _remove_lru(self) -> None:
        """Remove least recently used entry."""
        if not self._entries:
            return

        # Find entry with oldest access time
        lru_id = min(
            self._entries.items(),
            key=lambda x: x[1].accessed_at,
        )[0]
        await self.invalidate(lru_id)


class CachedResource(BaseResource):
    """Cached resource implementation.

    This class provides a cached resource implementation that wraps another resource.
    """

    def __init__(
        self,
        resource: BaseResource,
        cache: ResourceCache,
        ttl: Optional[int] = None,
    ) -> None:
        """Initialize resource.

        Args:
            resource: Resource to cache
            cache: Resource cache
            ttl: Time to live in seconds
        """
        super().__init__(
            resource.id,
            resource.type,
            name=resource.metadata.name,
            description=resource.metadata.description,
            version=resource.metadata.version,
            tags=resource.metadata.tags,
            dependencies=resource.metadata.dependencies,
            custom=resource.metadata.custom,
        )
        self._resource = resource
        self._cache = cache
        self._ttl = ttl

    async def _load(self) -> None:
        """Load resource data."""
        # Try to get from cache first
        cached = await self._cache.get(self.id)
        if cached is not None:
            self._state = cached.state
            self.metadata.updated_at = cached.metadata.updated_at
            return

        # Load from underlying resource
        await self._resource.load()
        self._state = self._resource.state
        self.metadata.updated_at = self._resource.metadata.updated_at

        # Update cache
        await self._cache.set(self._resource, ttl=self._ttl)

    async def _save(self) -> None:
        """Save resource data."""
        # Save to underlying resource
        await self._resource.save()
        self.metadata.updated_at = self._resource.metadata.updated_at

        # Update cache
        await self._cache.set(self._resource, ttl=self._ttl)

    async def _delete(self) -> None:
        """Delete resource data."""
        # Delete from underlying resource
        await self._resource.delete()

        # Invalidate cache
        await self._cache.invalidate(self.id)

    async def _initialize(self) -> None:
        """Initialize resource."""
        await self._resource._initialize()

    async def _execute(self) -> None:
        """Execute resource."""
        await self._resource._execute()

    async def _cleanup(self) -> None:
        """Clean up resource."""
        await self._resource._cleanup()
        await self._cache.invalidate(self.id)
