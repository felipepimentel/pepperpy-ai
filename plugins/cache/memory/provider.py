"""Memory cache provider implementation."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Self, TypeVar

from pepperpy.cache.provider import CacheError, CacheProvider
from pepperpy.plugin.provider import BasePluginProvider

T = TypeVar("T")


@dataclass
class CacheEntry:
    """Entry in the cache."""

    key: str
    value: Any
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return self.expires_at is not None and datetime.now() > self.expires_at


class MemoryCacheProvider(CacheProvider, BasePluginProvider):
    """In-memory cache provider implementation."""

    # Type-annotated config attributes
    max_entries: int = 10000
    default_ttl: int = 3600

    # Private state fields
    _entries: dict[str, CacheEntry]
    _tags: dict[str, set[str]]

    async def __aenter__(self) -> Self:
        """Enter async context manager.

        This allows the provider to be used with async with.
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager.

        This ensures resources are properly cleaned up when the context is exited.
        """
        await self.cleanup()

    def __repr__(self) -> str:
        """Return string representation of provider."""
        initialized = getattr(self, "initialized", False)
        entry_count = len(getattr(self, "_entries", {}))
        return (
            f"MemoryCacheProvider(initialized={initialized}, "
            f"max_entries={self.max_entries}, default_ttl={self.default_ttl}, "
            f"current_entries={entry_count})"
        )

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        if self.initialized:
            return

        # Initialize state
        self.initialized = True

        # Get configuration from attributes (already set from config)
        self.max_entries = self.config.get("max_entries", self.max_entries)
        self.default_ttl = self.config.get("default_ttl", self.default_ttl)

        # Validate configuration
        if self.max_entries <= 0:
            raise CacheError("max_entries must be greater than 0")
        if self.default_ttl < 0:
            raise CacheError("default_ttl cannot be negative")

        # Initialize cache storage
        self._entries = {}
        self._tags = {}

        self.logger.debug(
            f"Memory cache provider initialized with max_entries={self.max_entries}, "
            f"default_ttl={self.default_ttl}"
        )

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        """
        # Clear cache storage
        if hasattr(self, "_entries"):
            self._entries.clear()
        if hasattr(self, "_tags"):
            self._tags.clear()

        self.initialized = False
        self.logger.debug("Memory cache provider cleaned up")

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a cache operation.

        Args:
            input_data: Task data containing:
                - task: Task name (get, set, delete, invalidate_tag, clear)
                - key: Cache key
                - value: Value to cache (for set)
                - ttl: Time to live in seconds (for set)
                - tags: Tags to associate with key (for set)
                - metadata: Additional metadata (for set)
                - tag: Tag to invalidate (for invalidate_tag)
                - default: Default value if key not found (for get)

        Returns:
            Operation result
        """
        if not self.initialized:
            await self.initialize()

        # Validate input
        if not isinstance(input_data, dict):
            raise CacheError("Input data must be a dictionary")

        task = input_data.get("task")

        if not task:
            return {"status": "error", "message": "No task specified"}

        try:
            if task == "get":
                key = input_data.get("key")
                default = input_data.get("default")

                if not key:
                    return {"status": "error", "message": "Key is required"}

                value = self.get(key, default)
                return {
                    "status": "success",
                    "value": value,
                    "found": value is not default,
                }

            elif task == "set":
                key = input_data.get("key")
                value = input_data.get("value")
                ttl = input_data.get("ttl", self.default_ttl)
                tags = input_data.get("tags", set())
                metadata = input_data.get("metadata", {})

                if not key:
                    return {"status": "error", "message": "Key is required"}

                if value is None:
                    return {"status": "error", "message": "Value is required"}

                # Validate ttl
                if ttl is not None and ttl < 0:
                    return {"status": "error", "message": "TTL cannot be negative"}

                # Convert tags to set if it's a list
                if isinstance(tags, list):
                    tags = set(tags)
                elif not isinstance(tags, set):
                    return {"status": "error", "message": "Tags must be a list or set"}

                # Check if we've reached max entries
                if len(self._entries) >= self.max_entries and key not in self._entries:
                    # Try to remove expired entries first
                    self.purge_expired_entries()

                    # Check again after purging
                    if (
                        len(self._entries) >= self.max_entries
                        and key not in self._entries
                    ):
                        raise CacheError("Cache capacity reached")

                self.set(key, value, ttl, tags, metadata)
                return {"status": "success", "message": "Value cached"}

            elif task == "delete":
                key = input_data.get("key")

                if not key:
                    return {"status": "error", "message": "Key is required"}

                self.delete(key)
                return {"status": "success", "message": "Key deleted"}

            elif task == "invalidate_tag":
                tag = input_data.get("tag")

                if not tag:
                    return {"status": "error", "message": "Tag is required"}

                self.invalidate_tag(tag)
                return {"status": "success", "message": "Tag invalidated"}

            elif task == "clear":
                purge_only = input_data.get("purge_only", False)

                if purge_only:
                    purged_count = self.purge_expired_entries()
                    return {
                        "status": "success",
                        "message": f"Purged {purged_count} expired entries",
                        "purged_count": purged_count,
                    }
                else:
                    self.clear()
                    return {"status": "success", "message": "Cache cleared"}

            elif task == "search":
                query = input_data.get("query")

                if not query or not isinstance(query, dict):
                    return {
                        "status": "error",
                        "message": "Valid query is required for search",
                    }

                results = self.search_by_metadata(query)
                return {"status": "success", "results": results, "count": len(results)}

            else:
                return {"status": "error", "message": f"Unknown task: {task}"}

        except CacheError as e:
            self.logger.error(f"Cache error during task '{task}': {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            self.logger.error(f"Error executing task '{task}': {e}")
            return {"status": "error", "message": f"Unexpected error: {e!s}"}

    def search_by_metadata(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Search cache entries by metadata criteria.

        Args:
            query: Dictionary of metadata keys and values to match

        Returns:
            List of matching entries (key, value, metadata)
        """
        results = []

        # Helper function to check if an entry matches the query
        def matches_query(entry: CacheEntry) -> bool:
            # Skip expired entries
            if entry.is_expired:
                return False

            # Check each query key/value against the entry's metadata
            for key, value in query.items():
                # Handle special operators
                if isinstance(value, dict) and len(value) == 1:
                    # Check for operator queries like {"$gt": 5}
                    op, op_value = next(iter(value.items()))

                    if op == "$gt":
                        if key not in entry.metadata or entry.metadata[key] <= op_value:
                            return False
                    elif op == "$lt":
                        if key not in entry.metadata or entry.metadata[key] >= op_value:
                            return False
                    elif op == "$in":
                        if (
                            key not in entry.metadata
                            or entry.metadata[key] not in op_value
                        ):
                            return False
                    elif op == "$exists":
                        exists = key in entry.metadata
                        if exists != op_value:
                            return False
                    else:
                        # Unknown operator
                        return False
                # Simple equality check
                elif key not in entry.metadata or entry.metadata[key] != value:
                    return False

            # All criteria matched
            return True

        # Find all matching entries
        for key, entry in self._entries.items():
            if matches_query(entry):
                results.append(
                    {
                        "key": key,
                        "value": entry.value,
                        "metadata": entry.metadata.copy(),
                        "expires_at": entry.expires_at.isoformat()
                        if entry.expires_at
                        else None,
                    }
                )

        return results

    def purge_expired_entries(self) -> int:
        """Remove all expired entries from the cache.

        Returns:
            Number of entries purged
        """
        if not self._entries:
            return 0

        # Find expired keys
        expired_keys = [key for key, entry in self._entries.items() if entry.is_expired]

        # Delete expired entries
        for key in expired_keys:
            self.delete(key)

        return len(expired_keys)

    def get(
        self,
        key: str,
        default: T | None = None,
    ) -> T | None:
        """Get value from cache."""
        entry = self._entries.get(key)
        if entry is None or entry.is_expired:
            if entry and entry.is_expired:
                # Clean up expired entry
                self.delete(key)
            return default
        return entry.value

    def set(
        self,
        key: str,
        value: T,
        ttl: int | None = None,
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set value in cache."""
        # Use default_ttl if ttl is None
        ttl_value = self.default_ttl if ttl is None else ttl

        expires_at = (
            datetime.now() + timedelta(seconds=ttl_value)
            if ttl_value is not None
            else None
        )
        entry = CacheEntry(
            key=key,
            value=value,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        self._entries[key] = entry

        # Update tag indices
        if tags:
            for tag in tags:
                if tag not in self._tags:
                    self._tags[tag] = set()
                self._tags[tag].add(key)

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._entries:
            # Remove from tag indices
            for tag_keys in self._tags.values():
                tag_keys.discard(key)
            del self._entries[key]

    def invalidate_tag(self, tag: str) -> None:
        """Invalidate all entries with tag."""
        if tag in self._tags:
            keys = self._tags[
                tag
            ].copy()  # Create a copy to avoid modification during iteration
            for key in keys:
                self.delete(key)
            del self._tags[tag]

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self._tags.clear()
