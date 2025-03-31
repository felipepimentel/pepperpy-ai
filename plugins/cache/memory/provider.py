"""Memory cache provider implementation."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set, TypeVar

from pepperpy.cache.provider import CacheProvider
from pepperpy.common import BaseLocalProvider

T = TypeVar("T")


@dataclass
class CacheEntry:
    """Entry in the cache."""

    key: str
    value: Any
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return self.expires_at is not None and datetime.now() > self.expires_at


class MemoryCacheProvider(CacheProvider, BaseLocalProvider):
    """In-memory cache provider implementation."""

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize memory cache provider."""
        super().__init__(config=config)
        self._entries: Dict[str, CacheEntry] = {}
        self._tags: Dict[str, Set[str]] = {}

    def initialize(self) -> None:
        """Initialize cache storage."""
        self._entries.clear()
        self._tags.clear()

    def cleanup(self) -> None:
        """Cleanup cache storage."""
        self._entries.clear()
        self._tags.clear()

    def get(
        self,
        key: str,
        default: Optional[T] = None,
    ) -> Optional[T]:
        """Get value from cache."""
        entry = self._entries.get(key)
        if entry is None or entry.is_expired:
            return default
        return entry.value

    def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set value in cache."""
        expires_at = (
            datetime.now() + timedelta(seconds=ttl) if ttl is not None else None
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
            keys = self._tags[tag]
            for key in keys:
                self.delete(key)
            del self._tags[tag]

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self._tags.clear()
