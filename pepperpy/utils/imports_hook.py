"""Import hook utilities.

This module provides utilities for managing Python import hooks and optimizations.
"""

import asyncio
import importlib.abc
import importlib.machinery
import importlib.util
import logging
import sys
from types import ModuleType
from typing import Any, cast

from pepperpy.core.base import BaseComponent
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.monitoring import MonitoringManager
from pepperpy.core.monitoring.types import MonitoringLevel
from pepperpy.utils.imports_cache import ImportCache
from pepperpy.utils.imports_profiler import ImportProfiler
from pepperpy.utils.modules import ModuleManager

logger = logging.getLogger(__name__)


class ImportHookError(Exception):
    """Import hook error."""

    def __init__(
        self, message: str, module: str, details: dict[str, Any] | None = None
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            module: Module name
            details: Optional error details
        """
        super().__init__(message)
        self.module = module
        self.details = details or {}


class CircularDependencyError(ImportHookError):
    """Circular dependency error."""

    def __init__(self, module: str, chain: list[str]) -> None:
        """Initialize error.

        Args:
            module: Module name
            chain: Import chain that caused the circular dependency
        """
        super().__init__(
            f"Circular dependency detected: {' -> '.join(chain + [module])}",
            module,
            {"chain": chain},
        )
        self.chain = chain


class ImportOptimizer(
    BaseComponent,
    LifecycleComponent,
    importlib.abc.MetaPathFinder,
    importlib.abc.Loader,
):
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
        module_manager: ModuleManager,
        name: str = "import_optimizer",
        max_cache_size: int | None = None,
        max_cache_entries: int | None = None,
        cache_ttl: float | None = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize optimizer.

        Args:
            module_manager: Module manager instance
            name: Component name
            max_cache_size: Optional maximum cache size in bytes
            max_cache_entries: Optional maximum number of cache entries
            cache_ttl: Optional cache time-to-live in seconds
            max_retries: Maximum number of import retry attempts
        """
        super().__init__(name)
        self._manager = module_manager
        self._monitoring = MonitoringManager(
            name=f"{name}_monitoring", export_interval=60.0
        )
        self._cache = ImportCache(
            max_size=max_cache_size,
            max_entries=max_cache_entries,
            ttl=cache_ttl,
        )
        self._hooks: list[importlib.abc.MetaPathFinder] = []
        self._profiler = ImportProfiler()
        self._import_stack: list[str] = []
        self._dependency_graph: dict[str, set[str]] = {}
        self._error_count: dict[str, int] = {}
        self._max_retries = max_retries

    async def initialize(self) -> None:
        """Initialize import optimizer."""
        await self._monitoring.initialize()
        sys.meta_path.insert(0, cast(importlib.abc.MetaPathFinder, self))
        self.logger.debug("Import optimizer initialized")

    async def cleanup(self) -> None:
        """Clean up import optimizer."""
        sys.meta_path.remove(cast(importlib.abc.MetaPathFinder, self))
        await self._monitoring.cleanup()
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

    def _update_dependency_graph(self, module: str, dependencies: set[str]) -> None:
        """Update dependency graph.

        Args:
            module: Module name
            dependencies: Module dependencies

        Raises:
            CircularDependencyError: If circular dependency is detected
        """
        self._dependency_graph[module] = dependencies

        # Check for new circular dependencies
        visited: set[str] = set()
        path: list[str] = []

        def visit(mod: str) -> None:
            """Visit module and its dependencies.

            Args:
                mod: Module name

            Raises:
                CircularDependencyError: If circular dependency is detected
            """
            if mod in path:
                # Found circular dependency
                start_idx = path.index(mod)
                chain = path[start_idx:]
                raise CircularDependencyError(mod, chain)

            if mod in visited:
                return

            visited.add(mod)
            path.append(mod)

            for dep in self._dependency_graph.get(mod, set()):
                visit(dep)

            path.pop()

        visit(module)

    def _handle_import_error(
        self, module: str, error: Exception, context: dict[str, Any]
    ) -> None:
        """Handle import error.

        Args:
            module: Module name
            error: Exception instance
            context: Error context

        Raises:
            ImportHookError: If error handling fails
        """
        # Increment error count
        self._error_count[module] = self._error_count.get(module, 0) + 1

        # Log error with context
        logger.error(
            f"Module import failed: {error}",
            extra={
                "module": module,
                "error": str(error),
                "context": context,
                "attempt": self._error_count[module],
            },
            exc_info=True,
        )

        # Check retry limit
        if self._error_count[module] >= self._max_retries:
            # Clear error count and raise
            self._error_count.pop(module, None)
            raise ImportHookError(
                f"Failed to import module after {self._max_retries} attempts: {error}",
                module,
                {
                    "error": str(error),
                    "context": context,
                    "attempts": self._max_retries,
                },
            )

    def register_hook(self, hook: importlib.abc.MetaPathFinder) -> None:
        """Register import hook.

        Args:
            hook: Import hook to register
        """
        if hook not in self._hooks:
            self._hooks.append(hook)
            sys.meta_path.insert(0, hook)

    def unregister_hook(self, hook: importlib.abc.MetaPathFinder) -> None:
        """Unregister import hook.

        Args:
            hook: Import hook to unregister
        """
        if hook in self._hooks:
            self._hooks.remove(hook)
            try:
                sys.meta_path.remove(hook)
            except ValueError:
                pass

    def find_spec(
        self,
        fullname: str,
        path: list[str] | None = None,
        target: ModuleType | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        """Find module specification.

        Args:
            fullname: Full module name
            path: Optional module search path
            target: Optional module to use as target

        Returns:
            Module specification or None if not found
        """
        # Track import attempt
        asyncio.create_task(
            self._monitoring.record_event(
                level=MonitoringLevel.INFO,
                source="import_optimizer",
                message=f"Import attempt: {fullname}",
                data={"path": path, "target": target and target.__name__},
            )
        )

        # Check if module is already cached
        cached_module = self._cache.get(fullname)
        if cached_module:
            return None

        # Check for circular imports
        try:
            self._check_circular_dependency(fullname)
        except CircularDependencyError as e:
            asyncio.create_task(
                self._monitoring.record_event(
                    level=MonitoringLevel.WARNING,
                    source="import_optimizer",
                    message=f"Circular import detected: {fullname}",
                    data={"chain": e.chain},
                )
            )
            raise

        # Add to import stack
        self._import_stack.append(fullname)

        try:
            # Start profiling
            self._profiler.start_import(fullname)
            try:
                # Let other finders handle the actual import
                return None
            finally:
                self._profiler.finish_import(fullname)
        finally:
            # Remove from import stack
            self._import_stack.pop()

    def exec_module(self, module: ModuleType) -> None:
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
            dependencies = self._manager.get_dependencies(name)

            # Update dependency graph
            self._update_dependency_graph(name, dependencies)

            # Finish profiling
            profile = self._profiler.finish_import(name, dependencies)

            # Cache module
            self._cache.set(name, module, dependencies)

            # Log successful import
            logger.info(
                f"Module imported successfully: {name}",
                extra={
                    "module": name,
                    "duration": profile.duration,
                    "memory_delta": profile.memory_delta,
                    "dependencies": list(dependencies),
                },
            )

        except Exception as e:
            # Finish profiling with error
            self._profiler.finish_import(name, error=str(e))

            # Handle import error
            self._handle_import_error(
                name,
                e,
                {"spec": spec},
            )
            raise ImportError(f"Failed to import {name}: {e}") from e

    def get_import_profiles(self) -> dict[str, Any]:
        """Get import profiles.

        Returns:
            Dictionary containing import profiles, analysis, dependency graph,
            and error counts
        """
        return {
            "profiles": self._profiler.get_all_profiles(),
            "analysis": self._profiler.analyze_imports(),
            "dependency_graph": self._dependency_graph,
            "error_counts": self._error_count,
        }

    def reload_module(self, module: str) -> ModuleType:
        """Reload module and its dependencies.

        Args:
            module: Module name to reload

        Returns:
            Reloaded module

        Raises:
            ImportError: If module cannot be reloaded
        """
        # Invalidate module and dependencies
        self._cache.invalidate(module)

        # Clear profiling data
        self._profiler.clear()

        # Reload module
        return importlib.reload(sys.modules[module])

    def invalidate_module(self, module: str) -> None:
        """Invalidate module in cache.

        Args:
            module: Module name to invalidate
        """
        self._cache.invalidate(module)

    def invalidate_path(self, path: str) -> None:
        """Invalidate module by path.

        Args:
            path: Module file path to invalidate
        """
        self._cache.invalidate_path(path)

    def clear_cache(self) -> None:
        """Clear import cache and profiles."""
        self._cache = ImportCache()
        self._profiler.clear()
        self._dependency_graph.clear()
        self._error_count.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        return self._cache.get_cache_stats()

    def get(self, name: str) -> ModuleType | None:
        """Get cached module.

        Args:
            name: Module name

        Returns:
            Cached module or None if not found
        """
        return self._cache.get(name)

    def set(
        self, name: str, module: ModuleType, dependencies: set[str] | None = None
    ) -> None:
        """Set cached module.

        Args:
            name: Module name
            module: Module instance
            dependencies: Optional module dependencies
        """
        self._cache.set(name, module, dependencies)
