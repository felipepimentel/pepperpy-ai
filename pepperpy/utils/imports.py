"""Import utilities.

This module provides utilities for managing imports and dependencies.
"""

import importlib
import logging
from functools import lru_cache
from importlib.util import find_spec
from types import ModuleType
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ImportError(Exception):
    """Import error."""

    def __init__(
        self, message: str, module: str, details: Optional[Dict[str, Any]] = None
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


class LazyModule:
    """Lazy module loader.

    This class provides lazy loading of modules to avoid circular imports
    and improve startup performance.
    """

    def __init__(self, name: str) -> None:
        """Initialize loader.

        Args:
            name: Module name
        """
        self._name = name
        self._module: Optional[ModuleType] = None

    def __getattr__(self, name: str) -> Any:
        """Get module attribute.

        Args:
            name: Attribute name

        Returns:
            Module attribute

        Raises:
            AttributeError: If attribute does not exist
            ImportError: If module import fails
        """
        if self._module is None:
            try:
                self._module = importlib.import_module(self._name)
            except Exception as e:
                logger.error(
                    f"Failed to import module: {e}",
                    extra={"module": self._name},
                    exc_info=True,
                )
                raise ImportError(
                    f"Failed to import module: {e}",
                    self._name,
                    {"error": str(e)},
                )

        try:
            return getattr(self._module, name)
        except AttributeError as e:
            logger.error(
                f"Module attribute not found: {e}",
                extra={"module": self._name, "attribute": name},
                exc_info=True,
            )
            raise AttributeError(f"Module '{self._name}' has no attribute '{name}'")


def lazy_import(module_name: str) -> LazyModule:
    """Create lazy module loader.

    Args:
        module_name: Module name

    Returns:
        Lazy module loader
    """
    return LazyModule(module_name)


@lru_cache(maxsize=1024)
def safe_import(module_name: str) -> Optional[ModuleType]:
    """Safely import module.

    Args:
        module_name: Module name

    Returns:
        Imported module or None if import fails
    """
    try:
        return importlib.import_module(module_name)
    except Exception as e:
        logger.warning(
            f"Failed to import module: {e}",
            extra={"module": module_name},
            exc_info=True,
        )
        return None


def get_module_dependencies(module: ModuleType) -> Set[str]:
    """Get module dependencies.

    Args:
        module: Module to analyze

    Returns:
        Set of module dependencies
    """
    dependencies = set()
    for name, value in vars(module).items():
        if isinstance(value, ModuleType):
            dependencies.add(value.__name__)
    return dependencies


def check_circular_imports(module: ModuleType) -> List[Tuple[str, str]]:
    """Check for circular imports.

    Args:
        module: Module to check

    Returns:
        List of circular import pairs
    """
    visited = set()
    path = []
    circular = []

    def visit(mod: ModuleType) -> None:
        """Visit module and its dependencies.

        Args:
            mod: Module to visit
        """
        name = mod.__name__
        if name in path:
            # Found circular import
            start = path.index(name)
            cycle = path[start:] + [name]
            for i in range(len(cycle) - 1):
                circular.append((cycle[i], cycle[i + 1]))
            return

        if name in visited:
            return

        visited.add(name)
        path.append(name)

        for dep in get_module_dependencies(mod):
            dep_mod = safe_import(dep)
            if dep_mod:
                visit(dep_mod)

        path.pop()

    visit(module)
    return circular


def validate_imports(module: ModuleType) -> bool:
    """Validate module imports.

    Args:
        module: Module to validate

    Returns:
        True if imports are valid
    """
    try:
        # Check for circular imports
        circular = check_circular_imports(module)
        if circular:
            logger.warning(
                "Circular imports detected",
                extra={"module": module.__name__, "circular": circular},
            )
            return False

        # Check dependencies
        deps = get_module_dependencies(module)
        for dep in deps:
            if not safe_import(dep):
                logger.warning(
                    "Missing dependency",
                    extra={"module": module.__name__, "dependency": dep},
                )
                return False

        return True

    except Exception as e:
        logger.error(
            f"Import validation failed: {e}",
            extra={"module": module.__name__},
            exc_info=True,
        )
        return False


def is_module_available(module_name: str) -> bool:
    """Check if module is available.

    Args:
        module_name: Module name

    Returns:
        True if module is available
    """
    return find_spec(module_name) is not None


def get_module_version(module_name: str) -> Optional[str]:
    """Get module version.

    Args:
        module_name: Module name

    Returns:
        Module version or None if not available
    """
    try:
        module = safe_import(module_name)
        if not module:
            return None

        return getattr(module, "__version__", None)
    except Exception:
        return None


def get_module_path(module_name: str) -> Optional[str]:
    """Get module file path.

    Args:
        module_name: Module name

    Returns:
        Module file path or None if not available
    """
    try:
        spec = find_spec(module_name)
        return spec.origin if spec else None
    except Exception:
        return None


def get_module_doc(module_name: str) -> Optional[str]:
    """Get module documentation.

    Args:
        module_name: Module name

    Returns:
        Module documentation or None if not available
    """
    try:
        module = safe_import(module_name)
        return module.__doc__ if module else None
    except Exception:
        return None


def get_module_attributes(module_name: str) -> Dict[str, Any]:
    """Get module public attributes.

    Args:
        module_name: Module name

    Returns:
        Dictionary of module attributes
    """
    try:
        module = safe_import(module_name)
        if not module:
            return {}

        return {
            name: value
            for name, value in vars(module).items()
            if not name.startswith("_")
        }
    except Exception:
        return {}
