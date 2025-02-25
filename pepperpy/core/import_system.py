"""Import optimization system.

This module provides a unified import system with features like:
- Efficient caching and lazy loading
- Circular import detection
- Import profiling and metrics
- Dependency tracking
"""

import importlib
import sys
import time
from typing import Any

from pepperpy.core.base import BaseComponent
from pepperpy.core.import_errors import CircularDependencyError
from pepperpy.core.utils import logger


class ImportMetadata:
    """Metadata for imported modules."""

    def __init__(
        self,
        name: str,
        path: str | None = None,
        dependencies: set[str] | None = None,
        import_time: float | None = None,
        memory_usage: int | None = None,
    ) -> None:
        """Initialize metadata.

        Args:
            name: Module name
            path: Optional module file path
            dependencies: Optional module dependencies
            import_time: Optional import time in seconds
            memory_usage: Optional memory usage in bytes
        """
        self.name = name
        self.path = path
        self.dependencies = dependencies or set()
        self.import_time = import_time
        self.memory_usage = memory_usage


class ImportCache:
    """Cache for imported modules."""

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
            ttl: Optional cache time-to-live in seconds
        """
        self._cache: dict[str, Any] = {}
        self._metadata: dict[str, ImportMetadata] = {}
        self._max_size = max_size
        self._max_entries = max_entries
        self._ttl = ttl
        self._hits = 0
        self._misses = 0

    def get(self, name: str) -> Any | None:
        """Get cached module.

        Args:
            name: Module name

        Returns:
            Optional[Any]: Cached module or None if not found
        """
        if name in self._cache:
            self._hits += 1
            return self._cache[name]
        self._misses += 1
        return None

    def set(
        self,
        name: str,
        module: Any,
        metadata: ImportMetadata | None = None,
    ) -> None:
        """Set cached module.

        Args:
            name: Module name
            module: Module instance
            metadata: Optional module metadata
        """
        if self._max_entries and len(self._cache) >= self._max_entries:
            # Remove oldest entry
            oldest = min(self._metadata.items(), key=lambda x: x[1].import_time or 0)
            self._cache.pop(oldest[0], None)
            self._metadata.pop(oldest[0], None)

        self._cache[name] = module
        if metadata:
            self._metadata[name] = metadata

    def invalidate(self, name: str) -> None:
        """Invalidate cached module.

        Args:
            name: Module name
        """
        self._cache.pop(name, None)
        self._metadata.pop(name, None)

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()
        self._metadata.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict[str, Any]: Cache statistics
        """
        return {
            "total_entries": len(self._cache),
            "total_size": sum(m.memory_usage or 0 for m in self._metadata.values()),
            "hits": self._hits,
            "misses": self._misses,
        }


class ImportOptimizer(BaseComponent):
    """Import optimizer for managing module imports.

    This class provides functionality for optimizing module imports by:
    - Caching loaded modules with file modification tracking
    - Detecting and preventing circular imports
    - Managing module dependencies
    - Providing lazy loading capabilities
    - Profiling import performance
    - Monitoring import activity
    """

    def __init__(
        self,
        name: str = "import_optimizer",
        max_cache_size: int | None = None,
        max_cache_entries: int | None = None,
        cache_ttl: float | None = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize optimizer.

        Args:
            name: Component name
            max_cache_size: Optional maximum cache size in bytes
            max_cache_entries: Optional maximum number of cache entries
            cache_ttl: Optional cache time-to-live in seconds
            max_retries: Maximum number of import retry attempts
        """
        super().__init__(name)
        self._cache = ImportCache(
            max_size=max_cache_size,
            max_entries=max_cache_entries,
            ttl=cache_ttl,
        )
        self._import_stack: list[str] = []
        self._dependency_graph: dict[str, set[str]] = {}
        self._error_count: dict[str, int] = {}
        self._max_retries = max_retries

    async def _initialize(self) -> None:
        """Initialize import optimizer."""
        sys.meta_path.insert(0, self)
        self.logger.debug("Import optimizer initialized")

    async def _cleanup(self) -> None:
        """Clean up import optimizer."""
        sys.meta_path.remove(self)
        self.logger.debug("Import optimizer cleaned up")

    def _check_circular_dependency(self, module: str) -> None:
        """Check for circular dependencies.

        Args:
            module: Module name to check

        Raises:
            CircularDependencyError: If circular dependency is detected
        """
        if module in self._import_stack:
            # Get the circular dependency chain
            start_idx = self._import_stack.index(module)
            chain = self._import_stack[start_idx:]
            raise CircularDependencyError(module, chain)

    def find_spec(
        self,
        fullname: str,
        path: list[str] | None = None,
        target: Any | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        """Find module specification.

        Args:
            fullname: Full module name
            path: Optional module search path
            target: Optional module to use as target

        Returns:
            Optional[importlib.machinery.ModuleSpec]: Module specification
        """
        # Check if module is already cached
        cached_module = self._cache.get(fullname)
        if cached_module:
            return None

        # Check for circular imports
        try:
            self._check_circular_dependency(fullname)
        except CircularDependencyError as e:
            logger.warning(
                f"Circular import detected: {fullname}",
                extra={"chain": e.chain},
            )
            raise

        # Add to import stack
        self._import_stack.append(fullname)

        try:
            # Start profiling
            start_time = time.time()
            try:
                # Let other finders handle the actual import
                return None
            finally:
                # Record import time
                import_time = time.time() - start_time
                logger.debug(
                    f"Import time for {fullname}: {import_time:.3f}s",
                    extra={"module": fullname, "import_time": import_time},
                )
        finally:
            # Remove from import stack
            self._import_stack.pop()

    def exec_module(self, module: Any) -> None:
        """Execute module.

        Args:
            module: Module to execute

        Raises:
            ImportError: If module cannot be imported
        """
        name = module.__name__
        spec = module.__spec__

        try:
            # Get original loader
            if spec and spec.loader and spec.loader is not self:
                # Execute with original loader
                spec.loader.exec_module(module)
            else:
                # Execute module code
                if not spec or not spec.origin:
                    raise ImportError(f"No module spec origin for {name}")

                origin = str(spec.origin)
                with open(origin) as f:
                    code = compile(f.read(), origin, "exec")
                exec(code, module.__dict__)

            # Get module dependencies
            dependencies = set()
            for key, value in module.__dict__.items():
                if isinstance(value, type(sys)):
                    dependencies.add(value.__name__)

            # Update dependency graph
            self._dependency_graph[name] = dependencies

            # Cache module
            metadata = ImportMetadata(
                name=name,
                path=spec and spec.origin,
                dependencies=dependencies,
                import_time=time.time(),
            )
            self._cache.set(name, module, metadata)

            # Log successful import
            logger.info(
                f"Module imported successfully: {name}",
                extra={
                    "module": name,
                    "dependencies": list(dependencies),
                },
            )

        except Exception as e:
            # Handle import error
            self._error_count[name] = self._error_count.get(name, 0) + 1
            if self._error_count[name] >= self._max_retries:
                self._error_count.pop(name, None)
                raise ImportError(
                    f"Failed to import {name} after {self._max_retries} attempts: {e}"
                ) from e
            raise ImportError(f"Failed to import {name}: {e}") from e

    def get_import_profiles(self) -> dict[str, Any]:
        """Get import profiles.

        Returns:
            Dict[str, Any]: Import profiles
        """
        return {
            "dependency_graph": self._dependency_graph,
            "error_counts": self._error_count,
            "cache_stats": self._cache.get_stats(),
        }

    def reload_module(self, name: str) -> Any:
        """Reload module and its dependencies.

        Args:
            name: Module name to reload

        Returns:
            Any: Reloaded module

        Raises:
            ImportError: If module cannot be reloaded
        """
        # Invalidate module and dependencies
        self._cache.invalidate(name)
        dependencies = self._dependency_graph.get(name, set())
        for dep in dependencies:
            self._cache.invalidate(dep)

        # Reload module
        return importlib.reload(sys.modules[name])

    def invalidate_module(self, name: str) -> None:
        """Invalidate module in cache.

        Args:
            name: Module name to invalidate
        """
        self._cache.invalidate(name)

    def clear_cache(self) -> None:
        """Clear import cache."""
        self._cache.clear()
        self._dependency_graph.clear()
        self._error_count.clear()


# Global optimizer instance
_optimizer: ImportOptimizer | None = None


def get_optimizer() -> ImportOptimizer:
    """Get global optimizer instance.

    Returns:
        ImportOptimizer: Global optimizer instance
    """
    global _optimizer
    if _optimizer is None:
        _optimizer = ImportOptimizer()
    return _optimizer


# Install optimizer
get_optimizer()
