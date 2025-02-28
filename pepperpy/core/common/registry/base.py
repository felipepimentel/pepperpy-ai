"""Registry system for component management.

This module provides the core registry functionality for managing components:

- Component registration and discovery
- Metadata management
- Component lifecycle tracking
- Dependency resolution
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID, uuid4

from ...errors import DuplicateError, NotFoundError

# Type definitions
ComponentID = UUID
Metadata = Dict[str, Any]

# Component type variable
T = TypeVar("T")


class ComponentMetadata:
    """Metadata for registered components."""

    def __init__(
        self,
        name: str,
        description: str = "",
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        """Initialize component metadata.

        Args:
            name: Component name
            description: Component description
            version: Component version
            tags: Component tags
            properties: Additional properties
        """
        self.name = name
        self.description = description
        self.version = version
        self.tags = tags or []
        self.properties = properties or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComponentMetadata":
        """Create metadata from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ComponentMetadata instance
        """
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version"),
            tags=data.get("tags", []),
            properties=data.get("properties", {}),
        )


class RegistryError(Exception):
    """Base class for registry errors."""

    pass


class ComponentNotFoundError(RegistryError, NotFoundError):
    """Error raised when a component is not found."""

    pass


class ComponentDuplicateError(RegistryError, DuplicateError):
    """Error raised when a component is already registered."""

    pass


class Registry(Generic[T]):
    """Registry for managing components."""

    def __init__(self):
        """Initialize registry."""
        self._components: Dict[ComponentID, T] = {}
        self._metadata: Dict[ComponentID, ComponentMetadata] = {}
        self._name_to_id: Dict[str, ComponentID] = {}

    def register(
        self, component: T, metadata: Optional[ComponentMetadata] = None
    ) -> ComponentID:
        """Register a component.

        Args:
            component: Component to register
            metadata: Component metadata

        Returns:
            Component ID

        Raises:
            ComponentDuplicateError: If component name is already registered
        """
        component_id = uuid4()
        component_name = getattr(component, "name", str(component_id))

        if component_name in self._name_to_id:
            raise ComponentDuplicateError(
                f"Component with name '{component_name}' already registered"
            )

        self._components[component_id] = component
        self._name_to_id[component_name] = component_id

        if metadata is None:
            metadata = ComponentMetadata(name=component_name)

        self._metadata[component_id] = metadata

        return component_id

    def unregister(self, component_id: ComponentID) -> None:
        """Unregister a component.

        Args:
            component_id: Component ID

        Raises:
            ComponentNotFoundError: If component is not found
        """
        if component_id not in self._components:
            raise ComponentNotFoundError(f"Component with ID {component_id} not found")

        component = self._components[component_id]
        component_name = getattr(component, "name", str(component_id))

        del self._components[component_id]
        del self._metadata[component_id]

        if component_name in self._name_to_id:
            del self._name_to_id[component_name]

    def get(self, component_id: ComponentID) -> T:
        """Get a component by ID.

        Args:
            component_id: Component ID

        Returns:
            Component

        Raises:
            ComponentNotFoundError: If component is not found
        """
        if component_id not in self._components:
            raise ComponentNotFoundError(f"Component with ID {component_id} not found")

        return self._components[component_id]

    def get_by_name(self, name: str) -> T:
        """Get a component by name.

        Args:
            name: Component name

        Returns:
            Component

        Raises:
            ComponentNotFoundError: If component is not found
        """
        if name not in self._name_to_id:
            raise ComponentNotFoundError(f"Component with name '{name}' not found")

        component_id = self._name_to_id[name]
        return self._components[component_id]

    def get_metadata(self, component_id: ComponentID) -> ComponentMetadata:
        """Get component metadata.

        Args:
            component_id: Component ID

        Returns:
            Component metadata

        Raises:
            ComponentNotFoundError: If component is not found
        """
        if component_id not in self._metadata:
            raise ComponentNotFoundError(f"Component with ID {component_id} not found")

        return self._metadata[component_id]

    def list(self) -> Dict[ComponentID, T]:
        """List all registered components.

        Returns:
            Dictionary of component ID to component
        """
        return dict(self._components)

    def list_metadata(self) -> Dict[ComponentID, ComponentMetadata]:
        """List all component metadata.

        Returns:
            Dictionary of component ID to metadata
        """
        return dict(self._metadata)

    def find_by_tag(self, tag: str) -> List[T]:
        """Find components by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of components with the specified tag
        """
        result = []
        for component_id, metadata in self._metadata.items():
            if tag in metadata.tags:
                result.append(self._components[component_id])
        return result

    def find_by_property(self, key: str, value: Any) -> List[T]:
        """Find components by property.

        Args:
            key: Property key
            value: Property value

        Returns:
            List of components with the specified property
        """
        result = []
        for component_id, metadata in self._metadata.items():
            if metadata.properties.get(key) == value:
                result.append(self._components[component_id])
        return result


class RegistryComponent(ABC):
    """Base class for components that can be registered."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get component name."""
        pass

    @property
    def metadata(self) -> ComponentMetadata:
        """Get component metadata."""
        return ComponentMetadata(name=self.name)


# Global registry instance
_registry: Optional[Registry[Any]] = None


def get_registry() -> Registry[Any]:
    """Get the global registry instance.

    Returns:
        Global registry instance
    """
    global _registry
    if _registry is None:
        _registry = Registry[Any]()
    return _registry


def auto_register(component: T) -> T:
    """Decorator to automatically register a component.

    Args:
        component: Component to register

    Returns:
        Registered component
    """
    registry = get_registry()
    registry.register(component)
    return component
