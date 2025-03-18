"""Registry for PepperPy components.

This module provides registry functionality for the PepperPy framework,
allowing components to be registered and discovered at runtime.
"""

from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.errors import PepperPyError

T = TypeVar("T")


class RegistryError(PepperPyError):
    """Error raised when a registry operation fails."""

    pass


class Registry:
    """Registry for storing and retrieving objects by name."""

    def __init__(self, name: str):
        """Initialize a registry.

        Args:
            name: The name of the registry
        """
        self.name = name
        self._items: Dict[str, Any] = {}

    def register(self, name: str, obj: Any) -> None:
        """Register an object.

        Args:
            name: The name to register the object under
            obj: The object to register

        Raises:
            RegistryError: If an object with the same name is already registered
        """
        if name in self._items:
            raise RegistryError(
                f"Object '{name}' already registered in registry '{self.name}'"
            )
        self._items[name] = obj

    def unregister(self, name: str) -> None:
        """Unregister an object.

        Args:
            name: The name of the object to unregister
        """
        if name in self._items:
            del self._items[name]

    def get(self, name: str) -> Optional[Any]:
        """Get an object.

        Args:
            name: The name of the object to get

        Returns:
            The object, or None if not found
        """
        return self._items.get(name)

    def get_all(self) -> Dict[str, Any]:
        """Get all objects.

        Returns:
            A dictionary of all objects in the registry
        """
        return self._items.copy()

    def list(self) -> List[str]:
        """List all registered object names.

        Returns:
            A list of all registered object names
        """
        return list(self._items.keys())

    def clear(self) -> None:
        """Clear the registry."""
        self._items.clear()


# Global registry of registries
_registries: Dict[str, Registry] = {}


def get_registry(name: str) -> Registry:
    """Get a registry by name, creating it if it doesn't exist.

    Args:
        name: The name of the registry

    Returns:
        The registry
    """
    if name not in _registries:
        _registries[name] = Registry(name)
    return _registries[name]


def register(registry_name: str, name: str, obj: Any) -> None:
    """Register an object in the specified registry.

    Args:
        registry_name: The name of the registry
        name: The name to register the object under
        obj: The object to register

    Raises:
        RegistryError: If an object with the same name is already registered
    """
    registry = get_registry(registry_name)
    registry.register(name, obj)


def unregister(registry_name: str, name: str) -> None:
    """Unregister an object from the specified registry.

    Args:
        registry_name: The name of the registry
        name: The name of the object to unregister
    """
    registry = get_registry(registry_name)
    registry.unregister(name)


def get(registry_name: str, name: str) -> Optional[Any]:
    """Get an object from the specified registry.

    Args:
        registry_name: The name of the registry
        name: The name of the object to get

    Returns:
        The object, or None if not found
    """
    registry = get_registry(registry_name)
    return registry.get(name)


def get_all(registry_name: str) -> Dict[str, Any]:
    """Get all objects from the specified registry.

    Args:
        registry_name: The name of the registry

    Returns:
        A dictionary of all objects in the registry
    """
    registry = get_registry(registry_name)
    return registry.get_all()


def list_registries() -> List[str]:
    """List all registry names.

    Returns:
        A list of all registry names
    """
    return list(_registries.keys())


def clear_registry(registry_name: str) -> None:
    """Clear a registry.

    Args:
        registry_name: The name of the registry
    """
    registry = get_registry(registry_name)
    registry.clear()


def clear_all_registries() -> None:
    """Clear all registries."""
    for registry in _registries.values():
        registry.clear()


__all__ = [
    "RegistryError",
    "Registry",
    "get_registry",
    "register",
    "unregister",
    "get",
    "get_all",
    "list_registries",
    "clear_registry",
    "clear_all_registries",
]
