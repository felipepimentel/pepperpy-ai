"""Utility functions for handling imports."""

import importlib
import sys
from typing import Any


def import_optional_dependency(name: str, version_requirement: str | None = None, extra: str | None = None) -> Any:
    """Import an optional dependency."""
    try:
        module = importlib.import_module(name)
        return module
    except ImportError:
        install_cmd = f"pip install {name}"
        if version_requirement:
            install_cmd += f">={version_requirement}"
        if extra:
            install_cmd = f"pip install pepperpy[{extra}]"
        msg = f"Optional dependency {name} is not available. Please install it with: {install_cmd}"
        print(msg, file=sys.stderr)
        return None


def safe_import(name: str) -> Any:
    """Safely import a module without raising ImportError."""
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


def lazy_import(name: str) -> Any:
    """Lazily import a module.

    This function returns a proxy object that will import the module
    only when it is first used.

    Args:
        name: Module name to import

    Returns:
        Any: Module proxy object
    """
    class ModuleProxy:
        """Proxy for lazy module import."""

        def __init__(self, module_name: str) -> None:
            """Initialize proxy.

            Args:
                module_name: Module name to import
            """
            self._module = None
            self._module_name = module_name

        def __getattr__(self, attr: str) -> Any:
            """Get module attribute.

            Args:
                attr: Attribute name

            Returns:
                Any: Attribute value

            Raises:
                AttributeError: If attribute not found
            """
            if self._module is None:
                self._module = importlib.import_module(self._module_name)
            return getattr(self._module, attr)

    return ModuleProxy(name)