"""Utility functions for safe imports in the Pepperpy framework.

This module provides functions for safely importing optional dependencies.
"""

import importlib
from typing import Any

from pepperpy.monitoring import logger


def safe_import(
    module_name: str,
    names: str | list[str],
    default: Any = None,
    package: str | None = None,
) -> Any:
    """Safely import an optional dependency.

    Args:
        module_name: The name of the module to import.
        names: A string or list of strings of the names to import from the module.
        default: The default value to return if the import fails.
        package: The package name to import from.

    Returns:
        The imported module/attributes or the default value if import fails.

    Example:
        >>> # Import a single name
        >>> BaseModel = safe_import("pydantic", "BaseModel")
        >>> # Import multiple names
        >>> Field, validator = safe_import("pydantic", ["Field", "validator"])
    """
    try:
        if isinstance(names, str):
            names = [names]

        # Handle package-relative imports
        if package:
            module = importlib.import_module(f"{package}.{module_name}")
        else:
            module = importlib.import_module(module_name)

        if len(names) == 1:
            return getattr(module, names[0])

        return tuple(getattr(module, name) for name in names)

    except (ImportError, AttributeError) as e:
        logger.warning(f"Failed to import {names} from {module_name}: {e!s}")

        if isinstance(default, tuple):
            return default
        elif len(names) == 1:
            return default
        else:
            return tuple(default for _ in names)


def lazy_import(
    module_name: str,
    names: str | list[str],
    package: str | None = None,
) -> Any:
    """Lazily import a module or specific names from a module.

    This function returns a proxy object that will import the module
    or names only when they are first accessed.

    Args:
        module_name: The name of the module to import.
        names: A string or list of strings of the names to import from the module.
        package: The package name to import from.

    Returns:
        A proxy object that will import the module/names when accessed.

    Example:
        >>> # Lazy import a single name
        >>> BaseModel = lazy_import("pydantic", "BaseModel")
        >>> # Lazy import multiple names
        >>> Field, validator = lazy_import("pydantic", ["Field", "validator"])
    """

    class LazyObject:
        def __init__(self) -> None:
            self._obj = None

        def __getattr__(self, name: str) -> Any:
            if self._obj is None:
                self._obj = safe_import(module_name, names, package=package)
            return getattr(self._obj, name)

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            if self._obj is None:
                self._obj = safe_import(module_name, names, package=package)
            if callable(self._obj):
                return self._obj(*args, **kwargs)
            raise TypeError(f"{self._obj} is not callable")

    return LazyObject()


__all__ = ["lazy_import", "safe_import"]
