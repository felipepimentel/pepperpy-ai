"""Utility functions for safe imports in the Pepperpy framework.

This module provides functions for safely importing optional dependencies.
"""

from typing import Any, Callable, List, Optional, Tuple, Union

from pepperpy.monitoring import logger


def safe_import(
    module_name: str,
    names: Union[str, List[str]],
    default: Any = None,
    package: Optional[str] = None,
) -> Any:
    """Safely import an optional dependency.

    Args:
        module_name: The name of the module to import.
        names: A string or list of strings of the names to import from the module.
        default: The default value to return if the import fails.
        package: The package name to import from.

    Returns:
        The imported module/attributes or the default value if import fails.
    """
    try:
        if isinstance(names, str):
            names = [names]
            
        module = __import__(module_name, fromlist=names, package=package)
        
        if len(names) == 1:
            return getattr(module, names[0])
        
        return tuple(getattr(module, name) for name in names)
        
    except (ImportError, AttributeError) as e:
        logger.warning(f"Failed to import {names} from {module_name}: {str(e)}")
        
        if isinstance(default, tuple):
            return default
        elif len(names) == 1:
            return default
        else:
            return tuple(default for _ in names)
