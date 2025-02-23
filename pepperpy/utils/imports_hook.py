"""Import hook utilities.

This module provides utilities for managing Python import hooks and optimizations.
"""

import importlib.abc
import importlib.machinery
import importlib.util
import logging
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

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


class ImportOptimizer(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Import optimizer for managing module imports.

    This class provides functionality for optimizing module imports by:
    - Caching loaded modules with file modification tracking
    - Detecting and preventing circular imports
    - Managing module dependencies
    - Providing lazy loading capabilities
    - Profiling import performance
    """

    def __init__(
        self,
        module_manager: ModuleManager,
        max_cache_size: int | None = None,
        max_cache_entries: int | None = None,
        cache_ttl: float | None = None,
    ) -> None:
        """Initialize optimizer.

        Args:
            module_manager: Module manager instance
            max_cache_size: Optional maximum cache size in bytes
            max_cache_entries: Optional maximum number of cache entries
            cache_ttl: Optional cache time-to-live in seconds
        """
        self._manager = module_manager
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
        self._max_retries = 3

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
        # Check if module is already cached
        if self._cache.get(fullname):
            return None

        # Check if module is being loaded (circular import)
        if self._cache.is_loading(fullname):
            raise ImportHookError(
                "Circular import detected",
                fullname,
                {"loading": list(self._cache._loading)},
            )

        # Try to find spec using registered hooks
        for hook in self._hooks:
            if spec := hook.find_spec(fullname, path, target):
                return spec

        # Try to find spec using default import machinery
        if path is None:
            path = sys.path

        for entry in path:
            if not entry:
                continue

            # Try source file
            source_path = Path(entry) / f"{fullname.replace('.', '/')}.py"
            if source_path.is_file():
                return importlib.machinery.ModuleSpec(
                    name=fullname,
                    loader=self,
                    origin=str(source_path),
                )

            # Try package directory
            package_path = Path(entry) / fullname.replace(".", "/")
            init_path = package_path / "__init__.py"
            if init_path.is_file():
                spec = importlib.machinery.ModuleSpec(
                    name=fullname,
                    loader=self,
                    origin=str(init_path),
                )
                spec._set_fileattr = True  # type: ignore
                spec.has_location = True
                spec.submodule_search_locations = [str(package_path)]
                return spec

        return None

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType | None:
        """Create module instance.

        Args:
            spec: Module specification

        Returns:
            Module instance or None to use default
        """
        return None

    def exec_module(self, module: ModuleType) -> None:
        """Execute module.

        Args:
            module: Module instance

        Raises:
            ImportHookError: If module execution fails
            CircularDependencyError: If circular dependency is detected
        """
        start_time = time.perf_counter()
        context: dict[str, Any] = {}

        try:
            # Start profiling
            self._profiler.start_import(module.__name__)

            # Check for circular dependencies
            self._check_circular_dependency(module.__name__)

            # Push module onto import stack
            self._import_stack.append(module.__name__)

            try:
                # Load module source
                spec = module.__spec__
                if not spec or not spec.origin:
                    error = "Invalid module specification"
                    context = {"spec": spec}
                    self._profiler.finish_import(
                        module.__name__,
                        error=error,
                    )
                    raise ImportHookError(
                        error,
                        module.__name__,
                        context,
                    )

                # Execute module code
                source = Path(spec.origin).read_text()
                code = compile(source, spec.origin, "exec")
                exec(code, module.__dict__)

                # Register module with manager
                self._manager.register_module(module)

                # Get dependencies
                dependencies = self._manager.get_dependencies(module.__name__)

                # Update dependency graph
                self._update_dependency_graph(module.__name__, dependencies)

                # Cache module
                self._cache.set(
                    module.__name__,
                    module,
                    dependencies,
                )

                # Finish profiling
                duration = time.perf_counter() - start_time
                self._profiler.finish_import(
                    module.__name__,
                    dependencies=dependencies,
                )

                # Log success
                logger.info(
                    f"Module imported successfully: {module.__name__}",
                    extra={
                        "module": module.__name__,
                        "duration": duration,
                        "dependencies": len(dependencies),
                    },
                )

            finally:
                # Pop module from import stack
                self._import_stack.pop()

        except CircularDependencyError:
            # Re-raise circular dependency errors
            raise

        except Exception as e:
            # Handle import error
            context["duration"] = time.perf_counter() - start_time
            self._handle_import_error(module.__name__, e, context)

            # Finish profiling with error
            self._profiler.finish_import(
                module.__name__,
                error=str(e),
            )
            raise

        finally:
            # Mark module as finished loading
            self._cache.finish_loading(module.__name__)

    def get_code(self, fullname: str) -> Any:
        """Get module code object.

        Args:
            fullname: Full module name

        Returns:
            Module code object
        """
        # This is required by the Loader ABC but we don't use it
        return None

    def get_import_profiles(self) -> dict[str, Any]:
        """Get import profiles.

        Returns:
            Dictionary containing import profiles and analysis
        """
        profiles = self._profiler.get_all_profiles()
        analysis = self._profiler.analyze_imports()

        return {
            "profiles": profiles,
            "analysis": analysis,
            "dependency_graph": self._dependency_graph,
            "error_counts": self._error_count,
        }

    def clear_profiles(self) -> None:
        """Clear all import profiles."""
        self._profiler.clear()
        self._error_count.clear()

    def reload_module(self, name: str) -> ModuleType | None:
        """Reload module.

        Args:
            name: Module name

        Returns:
            Reloaded module or None if reload fails
        """
        try:
            # Clear error count
            self._error_count.pop(name, None)

            # Reload module
            module = self._cache.get(name)
            if not module:
                return None

            # Clear profiles
            self._profiler.clear()

            # Re-execute module
            self.exec_module(module)
            return module

        except Exception as e:
            logger.error(
                f"Module reload failed: {e}",
                extra={"module": name},
                exc_info=True,
            )
            return None

    def reload_dependencies(self, name: str) -> set[str]:
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

            # Reload dependencies first
            for dep in self._dependency_graph.get(module_name, set()):
                reload_recursive(dep)

            # Reload module
            if self.reload_module(module_name):
                reloaded.add(module_name)

        reload_recursive(name)
        return reloaded

    def get_dependent_modules(self, path: str) -> set[str]:
        """Get modules that depend on a file.

        Args:
            path: Module file path

        Returns:
            Set of dependent module names
        """
        return self._cache.get_dependent_modules(path)

    def invalidate_cache(self, name: str) -> None:
        """Invalidate cached module.

        Args:
            name: Module name
        """
        self._cache.invalidate(name)
        self._dependency_graph.pop(name, None)
        self._error_count.pop(name, None)

    def invalidate_path(self, path: str) -> None:
        """Invalidate module by path.

        Args:
            path: Module file path
        """
        self._cache.invalidate_path(path)

    def clear_cache(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._dependency_graph.clear()
        self._error_count.clear()
