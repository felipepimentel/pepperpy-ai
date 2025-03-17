"""Registry for PepperPy components.

This module provides registry functionality for the PepperPy framework,
allowing components to be registered and discovered at runtime.
"""

from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T")
_registry: Dict[str, Dict[str, Any]] = {}


def register(registry_name: str, name: str, obj: Any) -> None:
    """Register an object in the specified registry.

    Args:
        registry_name: The name of the registry
        name: The name to register the object under
        obj: The object to register
    """
    if registry_name not in _registry:
        _registry[registry_name] = {}
    _registry[registry_name][name] = obj


def get(registry_name: str, name: str) -> Optional[Any]:
    """Get an object from the specified registry.

    Args:
        registry_name: The name of the registry
        name: The name of the object to get

    Returns:
        The object, or None if not found
    """
    if registry_name not in _registry:
        return None
    return _registry[registry_name].get(name)


def get_all(registry_name: str) -> Dict[str, Any]:
    """Get all objects from the specified registry.

    Args:
        registry_name: The name of the registry

    Returns:
        A dictionary of all objects in the registry
    """
    if registry_name not in _registry:
        return {}
    return _registry[registry_name].copy()


__all__ = ["register", "get", "get_all"]
