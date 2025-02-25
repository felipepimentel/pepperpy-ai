"""Import utilities.

This module provides utilities for managing imports, including:
- Lazy imports
- Safe imports
- Import validation
- Module dependencies
- Circular import detection
- Import profiling
"""

"""Import utilities."""
import importlib
import importlib.util
import sys
import time
import types
import warnings
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

from pepperpy.core.errors import PepperpyError


class ImportError(PepperpyError):
    """Base class for import-related errors."""


class CircularImportError(ImportError):
    """Error raised when a circular import is detected."""

    def __init__(self, cycle: List[str]) -> None:
        """Initialize error.

        Args:
            cycle: List of module names forming the cycle
        """
        super().__init__(f"Circular import detected: {" -> ".join(cycle)}")
        self.cycle = cycle


class ModuleNotFoundError(ImportError):
    """Error raised when a module cannot be found."""

    def __init__(self, module_name: str) -> None:
        """Initialize error.

        Args:
            module_name: Name of the module that could not be found
        """
        super().__init__(f"Module not found: {module_name}")
        self.module_name = module_name


class ImportSystem:
    """System for managing imports and dependencies."""

    def __init__(self) -> None:
        """Initialize the import system."""
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._import_times: Dict[str, float] = {}
        self._hooks: List[Callable[[str], None]] = []

    def register_hook(self, hook: Callable[[str], None]) -> None:
        """Register an import hook.

        Args:
            hook: Function to call when a module is imported
        """
        self._hooks.append(hook)

    def track_import(self, module_name: str, dependencies: Set[str]) -> None:
        """Track module dependencies.

        Args:
            module_name: Name of the module
            dependencies: Set of module names that this module depends on
        """
        self._dependencies[module_name].update(dependencies)

    def get_dependencies(self, module_name: str) -> Set[str]:
        """Get dependencies for a module.

        Args:
            module_name: Name of the module

        Returns:
            Set of module names that this module depends on
        """
        return self._dependencies[module_name]

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular imports in the dependency graph.

        Returns:
            List of cycles found in the dependency graph
        """
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        path: List[str] = []

        def visit(module: str) -> None:
            if module in path:
                cycle = path[path.index(module):]
                cycle.append(module)
                cycles.append(cycle)
                return
            if module in visited:
                return

            visited.add(module)
            path.append(module)

            for dep in self._dependencies[module]:
                visit(dep)

            path.pop()

        for module in self._dependencies:
            visit(module)

        return cycles

    def profile_import(self, module_name: str) -> float:
        """Get import time for a module.

        Args:
            module_name: Name of the module

        Returns:
            Time in seconds taken to import the module
        """
        return self._import_times.get(module_name, 0.0)


class ImportManager:
    """Manager for handling imports safely and efficiently."""

    def __init__(self) -> None:
        """Initialize the import manager."""
        self._system = ImportSystem()
        self._cache: Dict[str, Any] = {}

    def lazy_import(
        self,
        module_name: str,
        attribute: Optional[str] = None,
        *,
        package: Optional[str] = None,
    ) -> Any:
        """Lazily import a module or attribute.

        Args:
            module_name: Name of the module to import
            attribute: Optional attribute to import from the module
            package: Optional package name for relative imports

        Returns:
            Imported module or attribute

        Raises:
            ModuleNotFoundError: If the module cannot be found
            ImportError: If there is an error during import
        """
        cache_key = f"{module_name}:{attribute}" if attribute else module_name

        if cache_key in self._cache:
            return self._cache[cache_key]

        start_time = time.time()

        try:
            module = importlib.import_module(module_name, package)
            if attribute:
                result = getattr(module, attribute)
            else:
                result = module

            self._cache[cache_key] = result
            self._system._import_times[module_name] = time.time() - start_time

            # Call import hooks
            for hook in self._system._hooks:
                hook(module_name)

            return result

        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(module_name) from e
        except Exception as e:
            raise ImportError(f"Error importing {module_name}: {e}") from e

    def safe_import(
        self,
        module_name: str,
        attribute: Optional[str] = None,
        *,
        default: Any = None,
        package: Optional[str] = None,
    ) -> Any:
        """Safely import a module or attribute.

        Args:
            module_name: Name of the module to import
            attribute: Optional attribute to import from the module
            default: Value to return if import fails
            package: Optional package name for relative imports

        Returns:
            Imported module/attribute or default value
        """
        try:
            return self.lazy_import(module_name, attribute, package=package)
        except (ModuleNotFoundError, ImportError):
            return default

    def analyze_imports(self) -> Dict[str, Dict[str, Any]]:
        """Analyze imports in the system.

        Returns:
            Dictionary containing import analysis results
        """
        cycles = self._system.detect_cycles()
        if cycles:
            warnings.warn(f"Circular imports detected: {cycles}")

        return {
            "dependencies": dict(self._system._dependencies),
            "import_times": dict(self._system._import_times),
            "circular_imports": cycles,
            "total_modules": len(self._system._dependencies),
            "total_dependencies": sum(len(deps) for deps in self._system._dependencies.values()),
        }


# Global instance
_import_manager = ImportManager()


def lazy_import(
    module_name: str,
    attribute: Optional[str] = None,
    *,
    package: Optional[str] = None,
) -> Any:
    """Global lazy import function.

    Args:
        module_name: Name of the module to import
        attribute: Optional attribute to import from the module
        package: Optional package name for relative imports

    Returns:
        Imported module or attribute
    """
    return _import_manager.lazy_import(module_name, attribute, package=package)


def safe_import(
    module_name: str,
    attribute: Optional[str] = None,
    *,
    default: Any = None,
    package: Optional[str] = None,
) -> Any:
    """Global safe import function.

    Args:
        module_name: Name of the module to import
        attribute: Optional attribute to import from the module
        default: Value to return if import fails
        package: Optional package name for relative imports

    Returns:
        Imported module/attribute or default value
    """
    return _import_manager.safe_import(module_name, attribute, default=default, package=package)


def analyze_imports() -> Dict[str, Dict[str, Any]]:
    """Global import analysis function.

    Returns:
        Dictionary containing import analysis results
    """
    return _import_manager.analyze_imports()
