"""Component registration for the PepperPy Hub.

This module provides functionality for registering and discovering components in the PepperPy Hub:
- Component registration: Register components with the hub
- Component discovery: Discover registered components
- Component validation: Validate component metadata and interfaces
- Component versioning: Track component versions and compatibility

The registration system enables the hub to maintain a catalog of available components,
facilitating discovery, dependency management, and version control.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, cast
from uuid import UUID, uuid4

from pepperpy.hub.base import HubArtifact


class ComponentType(Enum):
    """Types of components that can be registered with the hub."""

    AGENT = "agent"
    TOOL = "tool"
    MODEL = "model"
    PIPELINE = "pipeline"
    MEMORY = "memory"
    CONNECTOR = "connector"
    EXTENSION = "extension"
    PLUGIN = "plugin"


class Component(HubArtifact):
    """Base class for components that can be registered with the hub."""

    def __init__(
        self,
        name: str,
        version: str,
        component_type: ComponentType,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        component_id: Optional[UUID] = None,
    ):
        """Initialize a component.

        Args:
            name: Component name
            version: Component version
            component_type: Component type
            description: Component description
            metadata: Additional metadata
            component_id: Component ID (generated if not provided)
        """
        super().__init__(str(component_id or uuid4()), metadata)
        self.name = name
        self.version = version
        self.type = component_type
        self.description = description
        self.id = component_id or UUID(self.artifact_id)

    def validate(self) -> bool:
        """Validate the component.

        Returns:
            True if valid, False otherwise
        """
        return bool(self.name and self.version and self.type)

    def serialize(self) -> Dict[str, Any]:
        """Serialize the component for storage.

        Returns:
            Serialized component data
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "version": self.version,
            "type": self.type.value,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "Component":
        """Deserialize component data.

        Args:
            data: Serialized component data

        Returns:
            Component instance
        """
        return cls(
            name=data["name"],
            version=data["version"],
            component_type=ComponentType(data["type"]),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
            component_id=UUID(data["id"]) if "id" in data else None,
        )


T = TypeVar("T", bound=Component)


class ComponentRegistry:
    """Registry for PepperPy components."""

    def __init__(self):
        """Initialize the component registry."""
        self._components: Dict[UUID, Component] = {}
        self._components_by_name: Dict[str, Dict[str, Component]] = {}

    def register(self, component: Component) -> UUID:
        """Register a component with the hub.

        Args:
            component: Component to register

        Returns:
            Component ID

        Raises:
            ValueError: If component is invalid or already registered
        """
        # Validate component
        if not component.name:
            raise ValueError("Component name is required")
        if not component.version:
            raise ValueError("Component version is required")
        if not component.type:
            raise ValueError("Component type is required")

        # Check if component already exists
        if (
            component.type.value in self._components_by_name
            and component.name in self._components_by_name[component.type.value]
        ):
            existing = self._components_by_name[component.type.value][component.name]
            if existing.version == component.version:
                raise ValueError(
                    f"Component {component.name} v{component.version} already registered"
                )

        # Generate ID if not provided
        if not component.id:
            component.id = uuid4()

        # Register component
        self._components[component.id] = component

        # Register by name and type
        if component.type.value not in self._components_by_name:
            self._components_by_name[component.type.value] = {}
        self._components_by_name[component.type.value][component.name] = component

        return component.id

    def unregister(self, component_id: UUID) -> None:
        """Unregister a component from the hub.

        Args:
            component_id: Component ID

        Raises:
            ValueError: If component is not registered
        """
        if component_id not in self._components:
            raise ValueError(f"Component {component_id} not registered")

        component = self._components[component_id]
        del self._components[component_id]

        if (
            component.type.value in self._components_by_name
            and component.name in self._components_by_name[component.type.value]
        ):
            del self._components_by_name[component.type.value][component.name]

    def get(self, component_id: UUID) -> Optional[Component]:
        """Get a component by ID.

        Args:
            component_id: Component ID

        Returns:
            Component or None if not found
        """
        return self._components.get(component_id)

    def get_by_name(
        self, name: str, component_type: ComponentType
    ) -> Optional[Component]:
        """Get a component by name and type.

        Args:
            name: Component name
            component_type: Component type

        Returns:
            Component or None if not found
        """
        if component_type.value not in self._components_by_name:
            return None
        return self._components_by_name[component_type.value].get(name)

    def get_all(
        self, component_type: Optional[ComponentType] = None
    ) -> List[Component]:
        """Get all registered components.

        Args:
            component_type: Filter by component type

        Returns:
            List of components
        """
        if component_type is None:
            return list(self._components.values())

        result = []
        for component in self._components.values():
            if component.type == component_type:
                result.append(component)
        return result

    def get_by_type(self, component_type: Type[T]) -> List[T]:
        """Get components by their class type.

        Args:
            component_type: Component class type

        Returns:
            List of components of the specified type
        """
        result = []
        for component in self._components.values():
            if isinstance(component, component_type):
                result.append(cast(T, component))
        return result


# Singleton instance
_registry = ComponentRegistry()


def register_component(component: Component) -> UUID:
    """Register a component with the hub.

    Args:
        component: Component to register

    Returns:
        Component ID
    """
    return _registry.register(component)


def unregister_component(component_id: UUID) -> None:
    """Unregister a component from the hub.

    Args:
        component_id: Component ID
    """
    _registry.unregister(component_id)


def get_component(component_id: UUID) -> Optional[Component]:
    """Get a component by ID.

    Args:
        component_id: Component ID

    Returns:
        Component or None if not found
    """
    return _registry.get(component_id)


def get_component_by_name(
    name: str, component_type: ComponentType
) -> Optional[Component]:
    """Get a component by name and type.

    Args:
        name: Component name
        component_type: Component type

    Returns:
        Component or None if not found
    """
    return _registry.get_by_name(name, component_type)


def get_all_components(
    component_type: Optional[ComponentType] = None,
) -> List[Component]:
    """Get all registered components.

    Args:
        component_type: Filter by component type

    Returns:
        List of components
    """
    return _registry.get_all(component_type)


def get_components_by_type(component_type: Type[T]) -> List[T]:
    """Get components by their class type.

    Args:
        component_type: Component class type

    Returns:
        List of components of the specified type
    """
    return _registry.get_by_type(component_type)


# Export public API
__all__ = [
    "Component",
    "ComponentType",
    "ComponentRegistry",
    "register_component",
    "unregister_component",
    "get_component",
    "get_component_by_name",
    "get_all_components",
    "get_components_by_type",
]
