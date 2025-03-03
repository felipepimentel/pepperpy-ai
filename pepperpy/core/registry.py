"""Central registry for system components

This module implements the central registry that manages all framework components,
providing:

- Component registration and discovery
- Lifecycle management
- Dependency resolution
- Metadata and configuration management
- Component validation
- State monitoring and tracking

The registry is a fundamental piece for maintaining cohesion and enabling extensibility
of the framework through a central control point. It serves as the backbone for
component management across the entire system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar
from uuid import uuid4

from pepperpy.core.errors import DuplicateError, NotFoundError
from pepperpy.core.types.base import BaseComponent, ComponentID, Metadata

T = TypeVar("T", bound=BaseComponent)


class Registry(Generic[T]):
    """Base class for component registries."""

    def __init__(self):
        self._components: Dict[ComponentID, T] = {}
        self._metadata: Dict[ComponentID, Metadata] = {}

    def register(
        self, component: T, metadata: Optional[Metadata] = None,
    ) -> ComponentID:
        """Register a component with optional metadata."""
        component_id = uuid4()

        if component_id in self._components:
            raise DuplicateError(f"Component with ID {component_id} already registered")

        self._components[component_id] = component
        self._metadata[component_id] = metadata or Metadata(
            id=component_id, name=getattr(component, "name", str(component_id)),
        )

        return component_id

    def unregister(self, component_id: ComponentID) -> None:
        """Unregister a component by ID."""
        if component_id not in self._components:
            raise NotFoundError(f"Component with ID {component_id} not found")

        del self._components[component_id]
        del self._metadata[component_id]

    def get(self, component_id: ComponentID) -> T:
        """Get a component by ID."""
        if component_id not in self._components:
            raise NotFoundError(f"Component with ID {component_id} not found")

        return self._components[component_id]

    def get_metadata(self, component_id: ComponentID) -> Metadata:
        """Get metadata for a component by ID."""
        if component_id not in self._metadata:
            raise NotFoundError(
                f"Metadata for component with ID {component_id} not found",
            )

        return self._metadata[component_id]

    def list(self) -> Dict[ComponentID, T]:
        """List all registered components."""
        return self._components.copy()

    def list_metadata(self) -> Dict[ComponentID, Metadata]:
        """List metadata for all registered components."""
        return self._metadata.copy()


class RegistryFactory(ABC, Generic[T]):
    """Factory for creating registries."""

    @abstractmethod
    def create_registry(self) -> Registry[T]:
        """Create a new registry instance."""


class TypeRegistry(Registry[Any]):
    """Registry for managing component types."""

    def __init__(self):
        super().__init__()
        self._types: Dict[str, Type[Any]] = {}

    def register_type(self, type_name: str, component_type: Type[Any]) -> None:
        """Register a component type."""
        if type_name in self._types:
            raise DuplicateError(f"Type {type_name} already registered")

        self._types[type_name] = component_type

    def unregister_type(self, type_name: str) -> None:
        """Unregister a component type."""
        if type_name not in self._types:
            raise NotFoundError(f"Type {type_name} not found")

        del self._types[type_name]

    def get_type(self, type_name: str) -> Type[Any]:
        """Get a component type by name."""
        if type_name not in self._types:
            raise NotFoundError(f"Type {type_name} not found")

        return self._types[type_name]

    def list_types(self) -> Dict[str, Type[Any]]:
        """List all registered component types."""
        return self._types.copy()


class RegistryManager:
    """Manager for multiple registries."""

    def __init__(self):
        self._registries: Dict[str, Registry[Any]] = {}

    def add_registry(self, name: str, registry: Registry[Any]) -> None:
        """Add a registry."""
        if name in self._registries:
            raise DuplicateError(f"Registry {name} already exists")

        self._registries[name] = registry

    def remove_registry(self, name: str) -> None:
        """Remove a registry."""
        if name not in self._registries:
            raise NotFoundError(f"Registry {name} not found")

        del self._registries[name]

    def get_registry(self, name: str) -> Registry[Any]:
        """Get a registry by name."""
        if name not in self._registries:
            raise NotFoundError(f"Registry {name} not found")

        return self._registries[name]

    def list_registries(self) -> Dict[str, Registry[Any]]:
        """List all registries."""
        return self._registries.copy()


def create_registry_manager() -> RegistryManager:
    """Create and configure a new registry manager instance."""
    return RegistryManager()


# Export all types
__all__ = [
    "Registry",
    "RegistryFactory",
    "RegistryManager",
    "TypeRegistry",
    "create_registry_manager",
]
