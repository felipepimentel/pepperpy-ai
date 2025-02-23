"""Core import system.

This module provides a unified interface for managing imports and dependencies
in the Pepperpy framework.
"""

import logging
from typing import Any

from pepperpy.utils.imports import (
    LazyModule,
    lazy_import,
    safe_import,
    validate_imports,
)
from pepperpy.utils.imports_cache import ImportCache
from pepperpy.utils.imports_hook import ImportOptimizer
from pepperpy.utils.imports_profiler import ImportProfiler
from pepperpy.utils.modules import ModuleManager

logger = logging.getLogger(__name__)


class ImportSystem:
    """Core import system for managing module imports and dependencies."""

    def __init__(
        self,
        max_cache_size: int | None = None,
        max_cache_entries: int | None = None,
        cache_ttl: float | None = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize import system.

        Args:
            max_cache_size: Optional maximum cache size in bytes
            max_cache_entries: Optional maximum number of cache entries
            cache_ttl: Optional cache time-to-live in seconds
            max_retries: Maximum number of import retry attempts
        """
        self._manager = ModuleManager()
        self._optimizer = ImportOptimizer(
            self._manager,
            max_cache_size=max_cache_size,
            max_cache_entries=max_cache_entries,
            cache_ttl=cache_ttl,
        )
        self._profiler = ImportProfiler()
        self._cache = ImportCache(
            max_size=max_cache_size,
            max_entries=max_cache_entries,
            ttl=cache_ttl,
        )

        # Register import hook
        self._optimizer.register_hook(self._optimizer)

    def lazy_import(self, module_name: str) -> LazyModule:
        """Create lazy module loader.

        Args:
            module_name: Module name

        Returns:
            Lazy module loader
        """
        return lazy_import(module_name)

    def safe_import(self, module_name: str) -> Any | None:
        """Safely import module.

        Args:
            module_name: Module name

        Returns:
            Imported module or None if import fails
        """
        return safe_import(module_name)

    def validate_imports(self, module_name: str) -> bool:
        """Validate module imports.

        Args:
            module_name: Module name

        Returns:
            True if imports are valid
        """
        module = self.safe_import(module_name)
        if not module:
            return False
        return validate_imports(module)

    def get_dependencies(self, module_name: str) -> set[str]:
        """Get module dependencies.

        Args:
            module_name: Module name

        Returns:
            Set of module dependencies
        """
        return self._manager.get_dependencies(module_name)

    def get_reverse_dependencies(self, module_name: str) -> set[str]:
        """Get modules that depend on this module.

        Args:
            module_name: Module name

        Returns:
            Set of dependent module names
        """
        return self._manager.get_reverse_dependencies(module_name)

    def get_dependency_order(self, modules: list[str] | None = None) -> list[str]:
        """Get modules in dependency order.

        Args:
            modules: Optional list of modules to order

        Returns:
            List of modules in dependency order
        """
        return self._manager.get_dependency_order(modules)

    def check_circular_imports(self, module_name: str) -> list[tuple[str, str]]:
        """Check for circular imports.

        Args:
            module_name: Module name

        Returns:
            List of circular import pairs
        """
        return self._manager.check_circular_imports(module_name)

    def get_import_profiles(self) -> dict[str, Any]:
        """Get import profiles.

        Returns:
            Dictionary containing:
            - profiles: Module import profiles
            - analysis: Import performance analysis
            - dependency_graph: Module dependency graph
            - error_counts: Import error counts
        """
        return self._optimizer.get_import_profiles()

    def analyze_imports(self) -> dict[str, Any]:
        """Analyze import profiles.

        Returns:
            Dictionary containing:
            - total_imports: Total number of imports
            - total_duration: Total import duration
            - average_duration: Average import duration
            - max_duration: Maximum import duration
            - error_count: Number of import errors
            - average_dependencies: Average number of dependencies
            - max_dependencies: Maximum number of dependencies
            - total_memory_impact: Total memory usage
            - average_memory_impact: Average memory usage
            - max_memory_impact: Maximum memory usage
        """
        return self._profiler.analyze_imports()

    def get_slow_imports(self, threshold: float = 0.1) -> list[Any]:
        """Get slow module imports.

        Args:
            threshold: Duration threshold in seconds

        Returns:
            List of slow import profiles containing:
            - module: Module name
            - duration: Import duration
            - memory_delta: Memory usage delta
            - dependencies: Module dependencies
            - errors: Import errors
        """
        return self._profiler.get_slow_imports(threshold)

    def reload_module(self, module_name: str) -> Any | None:
        """Reload module.

        Args:
            module_name: Module name

        Returns:
            Reloaded module or None if reload fails
        """
        return self._optimizer.reload_module(module_name)

    def reload_dependencies(self, module_name: str) -> set[str]:
        """Reload module and its dependencies.

        Args:
            module_name: Module name

        Returns:
            Set of reloaded module names
        """
        return self._optimizer.reload_dependencies(module_name)

    def invalidate_module(self, module_name: str) -> None:
        """Invalidate module in cache.

        Args:
            module_name: Module name
        """
        self._optimizer.invalidate_cache(module_name)

    def invalidate_path(self, path: str) -> None:
        """Invalidate module by path.

        Args:
            path: Module file path
        """
        self._optimizer.invalidate_path(path)

    def clear_cache(self) -> None:
        """Clear import cache and profiles."""
        self._cache.clear()
        self._profiler.clear()
        self._optimizer.clear_cache()

    def __del__(self) -> None:
        """Cleanup import system."""
        self._optimizer.unregister_hook(self._optimizer)


# Global import system instance
_import_system = ImportSystem()


def get_import_system() -> ImportSystem:
    """Get global import system instance.

    Returns:
        Import system instance
    """
    return _import_system
