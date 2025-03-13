"""Core functionality for component registry in PepperPy.

This module provides the core functionality for the component registry in PepperPy,
including registration, discovery, and management of components.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pepperpy.errors import NotFoundError, ValidationError
from pepperpy.registry.base import Registry as BaseRegistry
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for component types
T = TypeVar("T")


class ComponentId:
    """Identifier for a component.

    A component ID uniquely identifies a component in the registry.
    """

    def __init__(
        self, name: str, version: Optional[str] = None, namespace: Optional[str] = None
    ):
        """Initialize a component ID.

        Args:
            name: The name of the component
            version: The version of the component
            namespace: The namespace of the component
        """
        self.name = name
        self.version = version
        self.namespace = namespace

    def __str__(self) -> str:
        """Get a string representation of the component ID.

        Returns:
            A string representation of the component ID
        """
        if self.namespace and self.version:
            return f"{self.namespace}/{self.name}@{self.version}"
        elif self.namespace:
            return f"{self.namespace}/{self.name}"
        elif self.version:
            return f"{self.name}@{self.version}"
        else:
            return self.name

    def __eq__(self, other: object) -> bool:
        """Check if this component ID is equal to another.

        Args:
            other: The other component ID

        Returns:
            True if the component IDs are equal, False otherwise
        """
        if not isinstance(other, ComponentId):
            return False
        return (
            self.name == other.name
            and self.version == other.version
            and self.namespace == other.namespace
        )

    def __hash__(self) -> int:
        """Get a hash of this component ID.

        Returns:
            A hash of this component ID
        """
        return hash((self.name, self.version, self.namespace))

    @classmethod
    def parse(cls, id_str: str) -> "ComponentId":
        """Parse a component ID from a string.

        Args:
            id_str: The string to parse

        Returns:
            A component ID

        Raises:
            ValueError: If the string cannot be parsed
        """
        # Split namespace and rest
        if "/" in id_str:
            namespace, rest = id_str.split("/", 1)
        else:
            namespace = None
            rest = id_str

        # Split name and version
        if "@" in rest:
            name, version = rest.split("@", 1)
        else:
            name = rest
            version = None

        return cls(name=name, version=version, namespace=namespace)


class ComponentMetadata:
    """Metadata for a component.

    Component metadata includes information about a component such as its
    description, dependencies, and other metadata.
    """

    def __init__(
        self,
        id: ComponentId,
        description: Optional[str] = None,
        dependencies: Optional[List[ComponentId]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize component metadata.

        Args:
            id: The component ID
            description: A description of the component
            dependencies: The dependencies of the component
            metadata: Additional metadata for the component
        """
        self.id = id
        self.description = description
        self.dependencies = dependencies or []
        self.metadata = metadata or {}

    def __str__(self) -> str:
        """Get a string representation of the component metadata.

        Returns:
            A string representation of the component metadata
        """
        return f"ComponentMetadata(id={self.id}, description={self.description})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the component metadata to a dictionary.

        Returns:
            A dictionary representation of the component metadata
        """
        return {
            "id": str(self.id),
            "description": self.description,
            "dependencies": [str(dep) for dep in self.dependencies],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComponentMetadata":
        """Create component metadata from a dictionary.

        Args:
            data: The dictionary to create the metadata from

        Returns:
            Component metadata

        Raises:
            ValueError: If the dictionary is invalid
        """
        try:
            id = ComponentId.parse(data["id"])
            description = data.get("description")
            dependencies = [
                ComponentId.parse(dep) for dep in data.get("dependencies", [])
            ]
            metadata = data.get("metadata", {})

            return cls(
                id=id,
                description=description,
                dependencies=dependencies,
                metadata=metadata,
            )
        except Exception as e:
            raise ValueError(f"Invalid component metadata: {e}")


class Component(Generic[T]):
    """A component in the registry.

    A component is a registered object with associated metadata.
    """

    def __init__(
        self,
        component: T,
        metadata: ComponentMetadata,
    ):
        """Initialize a component.

        Args:
            component: The component object
            metadata: The component metadata
        """
        self.component = component
        self.metadata = metadata

    def __str__(self) -> str:
        """Get a string representation of the component.

        Returns:
            A string representation of the component
        """
        return f"Component(id={self.metadata.id})"


class Registry(BaseRegistry[T]):
    """Registry for components.

    A registry manages components of a specific type, allowing for registration,
    discovery, and retrieval of components.
    """

    def __init__(self, component_type: Type[T]):
        """Initialize a registry.

        Args:
            component_type: The type of components in the registry
        """
        super().__init__(
            registry_name=f"{component_type.__name__}_registry",
            registry_type=component_type.__name__,
        )
        self.component_type = component_type
        self.components: Dict[ComponentId, Component[T]] = {}

    def register(
        self,
        component: T,
        id: Union[str, ComponentId],
        description: Optional[str] = None,
        dependencies: Optional[List[Union[str, ComponentId]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Component[T]:
        """Register a component.

        Args:
            component: The component to register
            id: The ID of the component
            description: A description of the component
            dependencies: The dependencies of the component
            metadata: Additional metadata for the component

        Returns:
            The registered component

        Raises:
            ValidationError: If the component is not of the correct type
            ValueError: If a component with the same ID is already registered
        """
        # Check component type
        if not isinstance(component, self.component_type):
            raise ValidationError(
                f"Component must be an instance of {self.component_type.__name__}",
                errors={
                    "component": f"Expected {self.component_type.__name__}, got {type(component).__name__}"
                },
            )

        # Parse the ID
        if isinstance(id, str):
            component_id = ComponentId.parse(id)
        else:
            component_id = id

        # Check if a component with the same ID is already registered
        if component_id in self.components:
            raise ValueError(f"Component {component_id} is already registered")

        # Parse dependencies
        if dependencies:
            parsed_deps = []
            for dep in dependencies:
                if isinstance(dep, str):
                    parsed_deps.append(ComponentId.parse(dep))
                else:
                    parsed_deps.append(dep)
        else:
            parsed_deps = []

        # Create component metadata
        component_metadata = ComponentMetadata(
            id=component_id,
            description=description,
            dependencies=parsed_deps,
            metadata=metadata,
        )

        # Create component
        component_wrapper = Component(
            component=component,
            metadata=component_metadata,
        )

        # Register component
        self.components[component_id] = component_wrapper

        logger.info(f"Registered component {component_id}")

        return component_wrapper

    def unregister(self, id: Union[str, ComponentId]) -> None:
        """Unregister a component.

        Args:
            id: The ID of the component to unregister

        Raises:
            NotFoundError: If the component is not registered
        """
        # Parse the ID
        if isinstance(id, str):
            component_id = ComponentId.parse(id)
        else:
            component_id = id

        # Check if the component exists
        if component_id not in self.components:
            raise NotFoundError(f"Component {component_id} not found")

        # Unregister the component
        del self.components[component_id]

        logger.info(f"Unregistered component {component_id}")

    def get(self, id: Union[str, ComponentId]) -> T:
        """Get a component.

        Args:
            id: The ID of the component to get

        Returns:
            The component

        Raises:
            NotFoundError: If the component is not registered
        """
        # Parse the ID
        if isinstance(id, str):
            component_id = ComponentId.parse(id)
        else:
            component_id = id

        # Get the component
        component = self.components.get(component_id)
        if component is None:
            raise NotFoundError(f"Component {component_id} not found")

        return component.component

    def get_metadata(self, id: Union[str, ComponentId]) -> ComponentMetadata:
        """Get component metadata.

        Args:
            id: The ID of the component to get metadata for

        Returns:
            The component metadata

        Raises:
            NotFoundError: If the component is not registered
        """
        # Parse the ID
        if isinstance(id, str):
            component_id = ComponentId.parse(id)
        else:
            component_id = id

        # Get the component
        component = self.components.get(component_id)
        if component is None:
            raise NotFoundError(f"Component {component_id} not found")

        return component.metadata

    def list(self) -> List[ComponentId]:
        """List registered component IDs.

        Returns:
            A list of registered component IDs
        """
        return list(self.components.keys())

    def list_components(self) -> List[Component[T]]:
        """List all registered components.

        Returns:
            A list of registered components
        """
        return list(self.components.values())

    def clear(self) -> None:
        """Clear the registry.

        This removes all registered components from the registry.
        """
        self.components.clear()
        logger.info(f"Cleared {self.component_type.__name__} registry")


class RegistryManager:
    """Manager for component registries.

    The registry manager manages multiple registries for different component types,
    providing a central interface for registration and discovery of components.
    """

    def __init__(self):
        """Initialize a registry manager."""
        self.registries: Dict[Type, Registry] = {}

    def get_registry(self, component_type: Type[T]) -> Registry[T]:
        """Get a registry for a component type.

        Args:
            component_type: The component type

        Returns:
            The registry for the component type
        """
        if component_type not in self.registries:
            self.registries[component_type] = Registry(component_type)

        return self.registries[component_type]

    def register(
        self,
        component: T,
        id: Union[str, ComponentId],
        component_type: Optional[Type[T]] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[Union[str, ComponentId]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Component[T]:
        """Register a component.

        Args:
            component: The component to register
            id: The ID of the component
            component_type: The component type, or None to use the component's type
            description: A description of the component
            dependencies: The dependencies of the component
            metadata: Additional metadata for the component

        Returns:
            The registered component
        """
        # Get the component type
        if component_type is None:
            component_type = type(component)

        # Get the registry for the component type
        registry = self.get_registry(component_type)

        # Register the component
        return registry.register(
            component=component,
            id=id,
            description=description,
            dependencies=dependencies,
            metadata=metadata,
        )

    def unregister(self, id: Union[str, ComponentId], component_type: Type) -> None:
        """Unregister a component.

        Args:
            id: The ID of the component to unregister
            component_type: The component type
        """
        # Get the registry for the component type
        registry = self.get_registry(component_type)

        # Unregister the component
        registry.unregister(id)

    def get(self, id: Union[str, ComponentId], component_type: Type[T]) -> T:
        """Get a component.

        Args:
            id: The ID of the component to get
            component_type: The component type

        Returns:
            The component
        """
        # Get the registry for the component type
        registry = self.get_registry(component_type)

        # Get the component
        return registry.get(id)

    def get_metadata(
        self, id: Union[str, ComponentId], component_type: Type
    ) -> ComponentMetadata:
        """Get component metadata.

        Args:
            id: The ID of the component to get metadata for
            component_type: The component type

        Returns:
            The component metadata
        """
        # Get the registry for the component type
        registry = self.get_registry(component_type)

        # Get the component metadata
        return registry.get_metadata(id)

    def list(self, component_type: Type) -> List[ComponentId]:
        """List registered component IDs.

        Args:
            component_type: The component type

        Returns:
            A list of registered component IDs
        """
        # Get the registry for the component type
        registry = self.get_registry(component_type)

        # List the components
        return registry.list()

    def list_components(self, component_type: Type[T]) -> List[Component[T]]:
        """List all registered components for a component type.

        Args:
            component_type: The component type

        Returns:
            A list of registered components
        """
        # Get the registry for the component type
        registry = self.get_registry(component_type)

        # List the components
        return registry.list_components()

    def clear(self, component_type: Optional[Type] = None) -> None:
        """Clear the registry.

        Args:
            component_type: The component type to clear, or None to clear all registries
        """
        if component_type is None:
            # Clear all registries
            for registry in self.registries.values():
                registry.clear()

            logger.info("Cleared all registries")
        else:
            # Get the registry for the component type
            registry = self.get_registry(component_type)

            # Clear the registry
            registry.clear()


# Global registry manager instance
_registry_manager: Optional[RegistryManager] = None


def get_registry_manager() -> RegistryManager:
    """Get the global registry manager instance.

    Returns:
        The global registry manager instance
    """
    global _registry_manager

    if _registry_manager is None:
        _registry_manager = RegistryManager()

    return _registry_manager
