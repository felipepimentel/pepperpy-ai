"""Import caching utilities.

This module provides advanced import caching with path-based caching and module reloading.
"""

import builtins
import importlib
import logging
import os
import time
from dataclasses import dataclass
from types import ModuleType

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

    def _evict_entries(self) -> None:
        """Evict cache entries based on constraints."""
        if not self._cache:
            return

        # Check TTL
        if self._ttl is not None:
            current_time = time.time()
            expired = [
                name
                for name, entry in self._cache.items()
                if current_time - entry.last_access > self._ttl
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
            return None

        # Update access time and count
        entry.last_access = time.time()
        entry.access_count += 1

        # Check if module file has been modified
        try:
            current_mtime = os.path.getmtime(entry.path)
            if current_mtime > entry.mtime:
                logger.info(
                    f"Module file modified: {name}",
                    extra={"module": name, "path": entry.path},
                )
                self.invalidate(name)
                return None

            # Check if any dependencies have been modified
            for dep in entry.dependencies:
                dep_entry = self._cache.get(dep)
                if not dep_entry:
                    continue
                try:
                    dep_mtime = os.path.getmtime(dep_entry.path)
                    if dep_mtime > entry.mtime:
                        logger.info(
                            f"Module dependency modified: {name} -> {dep}",
                            extra={"module": name, "dependency": dep},
                        )
                        self.invalidate(name)
                        return None
                except OSError:
                    continue

        except OSError:
            # File not found or inaccessible
            self.invalidate(name)
            return None

        return entry.module

    def set(
        self,
        name: str,
        module: ModuleType,
        dependencies: set[str] | None = None,
    ) -> None:
        """Set cached module.

        Args:
            name: Module name
            module: Module instance
            dependencies: Optional module dependencies
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

    def reload(self, name: str) -> ModuleType | None:
        """Reload module.

        Args:
            name: Module name

        Returns:
            Reloaded module or None if reload fails
        """
        entry = self._cache.get(name)
        if not entry:
            return None

        try:
            # Reload module
            module = importlib.reload(entry.module)

            # Update cache
            self.set(name, module, entry.dependencies)

            logger.info(
                f"Reloaded module: {name}",
                extra={"module": name, "path": entry.path},
            )
            return module

        except Exception as e:
            logger.error(
                f"Module reload failed: {e}",
                extra={"module": name},
                exc_info=True,
            )
            self.invalidate(name)
            return None

    def reload_dependencies(self, name: str) -> builtins.set[str]:
        """Reload module and its dependencies.

        Args:
            name: Module name

        Returns:
            Set of reloaded module names
        """
        reloaded = set()
        visited = set()

        def reload_recursive(module_name: str) -> None:
            """Recursively reload module and its dependencies.

            Args:
                module_name: Module name
            """
            if module_name in visited:
                return

            visited.add(module_name)
            entry = self._cache.get(module_name)
            if not entry:
                return

            # Reload dependencies first
            for dep in entry.dependencies:
                reload_recursive(dep)

            # Reload module
            if self.reload(module_name):
                reloaded.add(module_name)

        reload_recursive(name)
        return reloaded

    def is_loading(self, name: str) -> bool:
        """Check if module is currently being loaded.

        Args:
            name: Module name

        Returns:
            True if module is being loaded
        """
        return name in self._loading

    def start_loading(self, name: str) -> None:
        """Mark module as being loaded.

        Args:
            name: Module name
        """
        self._loading.add(name)

    def finish_loading(self, name: str) -> None:
        """Mark module as finished loading.

        Args:
            name: Module name
        """
        self._loading.discard(name)

    def get_path(self, name: str) -> str | None:
        """Get module file path.

        Args:
            name: Module name

        Returns:
            Module file path or None if not found
        """
        entry = self._cache.get(name)
        return entry.path if entry else None

    def get_dependencies(self, name: str) -> builtins.set[str]:
        """Get module dependencies.

        Args:
            name: Module name

        Returns:
            Set of module dependencies
        """
        entry = self._cache.get(name)
        return entry.dependencies if entry else set()

    def get_dependent_modules(self, path: str) -> builtins.set[str]:
        """Get modules that depend on a file.

        Args:
            path: Module file path

        Returns:
            Set of dependent module names
        """
        name = self._path_cache.get(path)
        if not name:
            return set()

        return {
            mod_name
            for mod_name, entry in self._cache.items()
            if name in entry.dependencies
        }

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._path_cache.clear()
        self._loading.clear()
        self._total_size = 0
