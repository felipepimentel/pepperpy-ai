"""Base Registry System

This module implements the core registry system that provides a unified
interface for component registration and discovery across the framework.
"""

import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
)
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# Type variable for registry components
T = TypeVar("T")


class RegistryError(Exception):
    """Base exception for registry errors."""

    pass


class ComponentNotFoundError(RegistryError):
    """Exception raised when a component is not found."""

    pass


class ComponentDuplicateError(RegistryError):
    """Exception raised when a component is already registered."""

    pass


@dataclass
class ComponentMetadata:
    """Metadata for a registered component."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    tags: Set[str] = field(default_factory=set)
    properties: Dict[str, Any] = field(default_factory=dict)


class RegistryComponent(ABC):
    """Base class for all registry components.

    All components that can be registered in the registry system
    should inherit from this class.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get component name."""
        pass

    @property
    def metadata(self) -> ComponentMetadata:
        """Get component metadata."""
        return ComponentMetadata(name=self.name)


class Registry(Generic[T]):
    """Unified registry for framework components.

    This class provides a generic registry implementation that can be used
    to register and discover components of a specific type.
    """

    def __init__(self, component_type: Type[T]):
        """Initialize registry.

        Args:
            component_type: Type of components managed by this registry
        """
        self._component_type = component_type
        self._components: Dict[str, T] = {}
        self._component_types: Dict[str, Type[T]] = {}
        self._metadata: Dict[str, ComponentMetadata] = {}

    def register(
        self, component: T, metadata: Optional[ComponentMetadata] = None
    ) -> None:
        """Register a component instance.

        Args:
            component: Component instance to register
            metadata: Optional component metadata

        Raises:
            ComponentDuplicateError: If component already registered
            TypeError: If component is not of the expected type
        """
        if not isinstance(component, self._component_type):
            raise TypeError(
                f"Component must be an instance of {self._component_type.__name__}"
            )

        name = getattr(component, "name", str(id(component)))

        if name in self._components:
            raise ComponentDuplicateError(f"Component '{name}' already registered")

        self._components[name] = component
        self._metadata[name] = metadata or getattr(
            component, "metadata", ComponentMetadata(name=name)
        )

        logger.debug(f"Registered component: {name}")

    def register_type(
        self,
        name: str,
        component_type: Type[T],
        metadata: Optional[ComponentMetadata] = None,
    ) -> None:
        """Register a component type.

        Args:
            name: Name to register the component type under
            component_type: Component type to register
            metadata: Optional component metadata

        Raises:
            ComponentDuplicateError: If component type already registered
            TypeError: If component type is not a subclass of the expected type
        """
        if not issubclass(component_type, self._component_type):
            raise TypeError(
                f"Component type must be a subclass of {self._component_type.__name__}"
            )

        if name in self._component_types:
            raise ComponentDuplicateError(f"Component type '{name}' already registered")

        self._component_types[name] = component_type
        self._metadata[name] = metadata or ComponentMetadata(name=name)

        logger.debug(f"Registered component type: {name}")

    def unregister(self, name: str) -> None:
        """Unregister a component or component type.

        Args:
            name: Component name

        Raises:
            ComponentNotFoundError: If component not found
        """
        if name in self._components:
            del self._components[name]
            del self._metadata[name]
            logger.debug(f"Unregistered component: {name}")
        elif name in self._component_types:
            del self._component_types[name]
            del self._metadata[name]
            logger.debug(f"Unregistered component type: {name}")
        else:
            raise ComponentNotFoundError(f"Component '{name}' not found")

    def get(self, name: str) -> T:
        """Get a registered component instance.

        Args:
            name: Component name

        Returns:
            Component instance

        Raises:
            ComponentNotFoundError: If component not found
        """
        if name not in self._components:
            raise ComponentNotFoundError(f"Component '{name}' not found")

        return self._components[name]

    def get_type(self, name: str) -> Type[T]:
        """Get a registered component type.

        Args:
            name: Component type name

        Returns:
            Component type

        Raises:
            ComponentNotFoundError: If component type not found
        """
        if name not in self._component_types:
            raise ComponentNotFoundError(f"Component type '{name}' not found")

        return self._component_types[name]

    def create(self, type_name: str, *args: Any, **kwargs: Any) -> T:
        """Create a component instance from a registered type.

        Args:
            type_name: Component type name
            *args: Positional arguments for component constructor
            **kwargs: Keyword arguments for component constructor

        Returns:
            Component instance

        Raises:
            ComponentNotFoundError: If component type not found
        """
        component_type = self.get_type(type_name)
        return component_type(*args, **kwargs)

    def get_metadata(self, name: str) -> ComponentMetadata:
        """Get metadata for a registered component or component type.

        Args:
            name: Component or component type name

        Returns:
            Component metadata

        Raises:
            ComponentNotFoundError: If component not found
        """
        if name not in self._metadata:
            raise ComponentNotFoundError(f"Component '{name}' not found")

        return self._metadata[name]

    def list_components(self) -> Dict[str, T]:
        """List all registered component instances.

        Returns:
            Dictionary mapping component names to instances
        """
        return self._components.copy()

    def list_component_types(self) -> Dict[str, Type[T]]:
        """List all registered component types.

        Returns:
            Dictionary mapping component type names to types
        """
        return self._component_types.copy()

    def list_metadata(self) -> Dict[str, ComponentMetadata]:
        """List metadata for all registered components and component types.

        Returns:
            Dictionary mapping component names to metadata
        """
        return self._metadata.copy()


class RegistryManager:
    """Manager for multiple registries.

    This class provides a central point for managing multiple registries
    of different component types.
    """

    _instance: Optional["RegistryManager"] = None

    def __init__(self):
        """Initialize registry manager."""
        self._registries: Dict[str, Registry[Any]] = {}

    @classmethod
    def get_instance(cls) -> "RegistryManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_registry(self, name: str, registry: Registry[Any]) -> None:
        """Register a registry.

        Args:
            name: Registry name
            registry: Registry instance

        Raises:
            ComponentDuplicateError: If registry already registered
        """
        if name in self._registries:
            raise ComponentDuplicateError(f"Registry '{name}' already registered")

        self._registries[name] = registry
        logger.debug(f"Registered registry: {name}")

    def unregister_registry(self, name: str) -> None:
        """Unregister a registry.

        Args:
            name: Registry name

        Raises:
            ComponentNotFoundError: If registry not found
        """
        if name not in self._registries:
            raise ComponentNotFoundError(f"Registry '{name}' not found")

        del self._registries[name]
        logger.debug(f"Unregistered registry: {name}")

    def get_registry(self, name: str) -> Registry[Any]:
        """Get a registry by name.

        Args:
            name: Registry name

        Returns:
            Registry instance

        Raises:
            ComponentNotFoundError: If registry not found
        """
        if name not in self._registries:
            raise ComponentNotFoundError(f"Registry '{name}' not found")

        return self._registries[name]

    def list_registries(self) -> Dict[str, Registry[Any]]:
        """List all registered registries.

        Returns:
            Dictionary mapping registry names to instances
        """
        return self._registries.copy()


def get_registry() -> RegistryManager:
    """Get the global registry manager instance.

    Returns:
        Registry manager instance
    """
    return RegistryManager.get_instance()


def auto_register(registry: Registry[Any], module: Any) -> List[str]:
    """Auto-register components from a module.

    This function scans a module for classes that inherit from the registry's
    component type and automatically registers them.

    Args:
        registry: Registry to register components in
        module: Module to scan for components

    Returns:
        List of registered component names
    """
    registered = []
    component_type = registry._component_type

    for name, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and issubclass(obj, component_type)
            and obj != component_type
            and not inspect.isabstract(obj)
        ):
            try:
                registry.register_type(name, obj)
                registered.append(name)
                logger.debug(f"Auto-registered component type: {name}")
            except (ComponentDuplicateError, TypeError) as e:
                logger.warning(f"Failed to auto-register {name}: {e}")

    return registered
