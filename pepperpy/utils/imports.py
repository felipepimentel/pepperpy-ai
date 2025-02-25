"""Import utilities.

This module provides utilities for handling imports.
"""

import importlib
from typing import Any


def lazy_import(module_name: str) -> Any:
    """Lazily import a module.

    This function attempts to import a module and returns None if the import fails.
    This is useful for optional dependencies that may not be installed.

    Args:
        module_name: Name of the module to import

    Returns:
        The imported module or None if import fails

    Example:
        >>> prometheus_client = lazy_import("prometheus_client")
        >>> if prometheus_client:
        ...     counter = prometheus_client.Counter("name", "help")
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


__all__ = ["lazy_import"]
