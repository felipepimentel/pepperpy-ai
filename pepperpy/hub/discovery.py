"""Component discovery for the PepperPy Hub.

This module provides functionality for discovering components in the PepperPy Hub:
- Local discovery: Find components in the local environment
- Remote discovery: Find components in remote repositories
- Dependency resolution: Resolve component dependencies
- Version compatibility: Check component version compatibility

The discovery system enables the hub to find and load components from various sources,
facilitating component reuse and integration.
"""

import importlib
import inspect
import os
import pkgutil
import sys
from typing import List, Set

from pepperpy.hub.registration import Component, register_component


class ComponentDiscovery:
    """Component discovery for the PepperPy Hub."""

    @staticmethod
    def discover_in_module(module_name: str) -> List[Component]:
        """Discover components in a module.

        Args:
            module_name: Module name

        Returns:
            List of discovered components

        """
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return []

        components = []
        for _name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Component)
                and obj != Component
                and not inspect.isabstract(obj)
            ):
                try:
                    # Create instance if possible
                    create_method = getattr(obj, "create", None)
                    if create_method is not None and callable(create_method):
                        component = create_method()
                    else:
                        # Skip if we can't instantiate
                        continue

                    # Register component
                    register_component(component)
                    components.append(component)
                except Exception:
                    # Skip if we can't instantiate
                    continue

        return components

    @staticmethod
    def discover_in_package(package_name: str) -> List[Component]:
        """Discover components in a package.

        Args:
            package_name: Package name

        Returns:
            List of discovered components

        """
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            return []

        components = []
        visited_modules: Set[str] = set()

        def visit_module(module_name: str) -> None:
            if module_name in visited_modules:
                return
            visited_modules.add(module_name)

            components.extend(ComponentDiscovery.discover_in_module(module_name))

        # Visit the package itself
        visit_module(package_name)

        # Visit all submodules
        if hasattr(package, "__path__"):
            for _, name, is_pkg in pkgutil.iter_modules(
                package.__path__, package.__name__ + ".",
            ):
                visit_module(name)
                if is_pkg:
                    ComponentDiscovery.discover_in_package(name)

        return components

    @staticmethod
    def discover_in_path(path: str) -> List[Component]:
        """Discover components in a file system path.

        Args:
            path: File system path

        Returns:
            List of discovered components

        """
        if not os.path.exists(path):
            return []

        # Add path to sys.path temporarily
        original_path = sys.path.copy()
        if path not in sys.path:
            sys.path.insert(0, path)

        components = []
        try:
            # Find all Python modules in the path
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py") and not file.startswith("_"):
                        module_path = os.path.join(root, file)
                        module_name = os.path.relpath(module_path, path).replace(
                            os.path.sep, ".",
                        )
                        module_name = module_name[:-3]  # Remove .py extension

                        components.extend(
                            ComponentDiscovery.discover_in_module(module_name),
                        )
        finally:
            # Restore original sys.path
            sys.path = original_path

        return components

    @staticmethod
    def discover_local() -> List[Component]:
        """Discover components in the local environment.

        Returns:
            List of discovered components

        """
        components = []

        # Discover in pepperpy package
        components.extend(ComponentDiscovery.discover_in_package("pepperpy"))

        # Discover in current directory
        components.extend(ComponentDiscovery.discover_in_path(os.getcwd()))

        return components


# Convenience functions
def discover_components_in_module(module_name: str) -> List[Component]:
    """Discover components in a module.

    Args:
        module_name: Module name

    Returns:
        List of discovered components

    """
    return ComponentDiscovery.discover_in_module(module_name)


def discover_components_in_package(package_name: str) -> List[Component]:
    """Discover components in a package.

    Args:
        package_name: Package name

    Returns:
        List of discovered components

    """
    return ComponentDiscovery.discover_in_package(package_name)


def discover_components_in_path(path: str) -> List[Component]:
    """Discover components in a file system path.

    Args:
        path: File system path

    Returns:
        List of discovered components

    """
    return ComponentDiscovery.discover_in_path(path)


def discover_local_components() -> List[Component]:
    """Discover components in the local environment.

    Returns:
        List of discovered components

    """
    return ComponentDiscovery.discover_local()


# Export public API
__all__ = [
    "ComponentDiscovery",
    "discover_components_in_module",
    "discover_components_in_package",
    "discover_components_in_path",
    "discover_local_components",
]
