"""Import caching utilities.

This module provides advanced import caching with path-based caching and module reloading.
"""

import logging
import os
import time
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry for a module."""

    module: ModuleType
    path: str
    mtime: float
    dependencies: set[str]
    last_access: float = 0.0
    access_count: int = 0
    size: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired.

        Returns:
            True if entry is expired
        """
        try:
            current_mtime = os.path.getmtime(self.path)
            return current_mtime > self.mtime
        except OSError:
            return True


class ImportCache:
    """Advanced import cache with path-based caching and module reloading."""

    def __init__(
        self,
        max_size: int | None = None,
        max_entries: int | None = None,
        ttl: float | None = None,
    ) -> None:
        """Initialize cache.

        Args:
            max_size: Optional maximum cache size in bytes
            max_entries: Optional maximum number of cache entries
            ttl: Optional time-to-live in seconds
        """
        self._cache: dict[str, CacheEntry] = {}
        self._path_cache: dict[str, str] = {}  # Maps paths to module names
        self._loading: set[str] = set()
        self._max_size = max_size
        self._max_entries = max_entries
        self._ttl = ttl
        self._total_size = 0
        self._hits = 0
        self._misses = 0

    def _get_module_size(self, module: ModuleType) -> int:
        """Get approximate module size in bytes.

        Args:
            module: Module instance

        Returns:
            Module size in bytes
        """
        try:
            # Get source file size
            spec = getattr(module, "__spec__", None)
            if spec and spec.origin:
                return os.path.getsize(spec.origin)
        except OSError:
            pass
        return 0

    def _check_entry_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired.

        Args:
            entry: Cache entry

        Returns:
            True if entry is expired
        """
        # Check TTL
        if self._ttl is not None:
            current_time = time.time()
            if current_time - entry.last_access > self._ttl:
                return True

        # Check file modification time
        if entry.is_expired:
            return True

        # Check dependencies
        for dep in entry.dependencies:
            dep_entry = self._cache.get(dep)
            if not dep_entry:
                continue
            if dep_entry.is_expired:
                return True

        return False

    def _evict_entries(self) -> None:
        """Evict cache entries based on constraints."""
        if not self._cache:
            return

        # Check TTL and file modifications
        expired = [
            name
            for name, entry in self._cache.items()
            if self._check_entry_expired(entry)
        ]
        for name in expired:
            self.invalidate(name)

        # Check max entries
        if self._max_entries is not None and len(self._cache) > self._max_entries:
            # Remove least recently used entries
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: (x[1].last_access, -x[1].access_count),
            )
            to_remove = len(self._cache) - self._max_entries
            for name, _ in sorted_entries[:to_remove]:
                self.invalidate(name)

        # Check max size
        if self._max_size is not None and self._total_size > self._max_size:
            # Remove entries until under limit
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: (x[1].last_access, -x[1].access_count),
            )
            for name, _ in sorted_entries:
                if self._total_size <= self._max_size:
                    break
                self.invalidate(name)

    def get(self, name: str) -> ModuleType | None:
        """Get cached module.

        Args:
            name: Module name

        Returns:
            Cached module or None if not found or outdated
        """
        entry = self._cache.get(name)
        if not entry:
            self._misses += 1
            return None

        # Check if entry is expired
        if self._check_entry_expired(entry):
            self.invalidate(name)
            self._misses += 1
            return None

        # Update access time and count
        entry.last_access = time.time()
        entry.access_count += 1
        self._hits += 1

        return entry.module

    def set(
        self,
        name: str,
        module: ModuleType,
        dependencies: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Set cached module.

        Args:
            name: Module name
            module: Module instance
            dependencies: Optional module dependencies
            metadata: Optional module metadata
        """
        spec = getattr(module, "__spec__", None)
        if not spec or not spec.origin:
            logger.warning(
                f"Module has no origin: {name}",
                extra={"module": name},
            )
            return

        path = spec.origin
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            logger.warning(
                f"Cannot access module file: {name}",
                extra={"module": name, "path": path},
            )
            return

        # Calculate module size
        size = self._get_module_size(module)

        # Create cache entry
        entry = CacheEntry(
            module=module,
            path=path,
            mtime=mtime,
            dependencies=dependencies or set(),
            last_access=time.time(),
            access_count=0,
            size=size,
            metadata=metadata or {},
        )

        # Update total size
        old_entry = self._cache.get(name)
        if old_entry:
            self._total_size -= old_entry.size
        self._total_size += size

        # Set cache entry
        self._cache[name] = entry
        self._path_cache[path] = name

        # Evict entries if needed
        self._evict_entries()

    def invalidate(self, name: str) -> None:
        """Invalidate cached module.

        Args:
            name: Module name
        """
        entry = self._cache.pop(name, None)
        if entry:
            self._path_cache.pop(entry.path, None)
            self._total_size -= entry.size

            # Invalidate dependent modules
            for mod_name, mod_entry in list(self._cache.items()):
                if name in mod_entry.dependencies:
                    self.invalidate(mod_name)

    def invalidate_path(self, path: str) -> None:
        """Invalidate module by path.

        Args:
            path: Module file path
        """
        name = self._path_cache.get(path)
        if name:
            self.invalidate(name)

    def get_dependent_modules(self, path: str) -> set[str]:
        """Get modules that depend on a file.

        Args:
            path: Module file path

        Returns:
            Set of dependent module names
        """
        dependents = set()
        name = self._path_cache.get(path)
        if not name:
            return dependents

        for mod_name, entry in self._cache.items():
            if name in entry.dependencies:
                dependents.add(mod_name)

        return dependents

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        return {
            "total_entries": len(self._cache),
            "total_size": self._total_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": self._hits / (self._hits + self._misses)
            if self._hits + self._misses > 0
            else 0.0,
            "average_size": self._total_size / len(self._cache) if self._cache else 0,
            "max_size": self._max_size,
            "max_entries": self._max_entries,
            "ttl": self._ttl,
        }

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._path_cache.clear()
        self._loading.clear()
        self._total_size = 0
        self._hits = 0
        self._misses = 0
