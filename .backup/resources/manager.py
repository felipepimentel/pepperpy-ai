"""Resource manager implementation.

This module provides the central resource manager that handles resource lifecycle,
dependencies, and state management.
"""

from typing import Any, Dict, List, Optional, Set, TypeVar
from uuid import UUID, uuid4

from pepperpy.core.base import BaseComponent
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.logging import get_logger

from .base import BaseResource, ResourceMetadata, ResourceState, ResourceType
from .providers import ResourceProvider

logger = get_logger(__name__)

# Type variable for resource-specific results
ResultT = TypeVar("ResultT")


class ResourceManager(BaseComponent):
    """Central manager for resource lifecycle and dependencies.

    This class provides a unified interface for creating, managing, and cleaning up
    resources, handling their dependencies and ensuring proper initialization order.

    Example:
        >>> manager = ResourceManager()
        >>> await manager.register_provider(
        ...     resource_type=ResourceType.STORAGE,
        ...     provider=StorageProvider(),
        ... )
        >>> resource = await manager.create_resource(
        ...     name="local_storage",
        ...     config={"path": "/tmp/storage"},
        ... )
        >>> assert resource.state.is_ready()

    """

    def __init__(self, id: Optional[UUID] = None) -> None:
        """Initialize the resource manager.

        Args:
            id: Optional manager ID

        """
        super().__init__(id or uuid4())
        self._resources: Dict[str, BaseResource] = {}
        self._providers: Dict[str, ResourceProvider] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._logger = logger.getChild(self.__class__.__name__)

    async def register_provider(
        self,
        resource_type: ResourceType,
        provider: ResourceProvider,
    ) -> None:
        """Register a resource provider.

        Args:
            resource_type: Type of resources this provider handles
            provider: Provider instance

        Raises:
            ValueError: If provider type is already registered

        """
        if resource_type.value in self._providers:
            raise ValueError(
                f"Provider for type {resource_type.value} already registered"
            )

        self._providers[resource_type.value] = provider
        self._logger.info(
            "Registered resource provider",
            extra={"provider_type": resource_type.value},
        )

    async def create_resource(
        self,
        name: str,
        config: Dict[str, Any],
        dependencies: Optional[List[str]] = None,
    ) -> BaseResource:
        """Create and initialize a resource.

        Args:
            name: Resource name
            config: Resource configuration
            dependencies: Optional list of resource dependencies

        Returns:
            Created and initialized resource

        Raises:
            ConfigurationError: If configuration is invalid
            StateError: If resource creation fails
            ValueError: If resource name already exists

        """
        if name in self._resources:
            raise ValueError(f"Resource {name} already exists")

        if "type" not in config:
            raise ConfigurationError("Resource type not specified in config")

        resource_type = ResourceType(config["type"])
        provider = self._providers.get(resource_type.value)
        if not provider:
            raise ConfigurationError(
                f"No provider registered for type {resource_type.value}"
            )

        # Record dependencies
        if dependencies:
            missing = [d for d in dependencies if d not in self._resources]
            if missing:
                raise ConfigurationError(
                    f"Dependencies not found: {', '.join(missing)}"
                )
            self._dependencies[name] = set(dependencies)

        try:
            # Create resource
            resource = await provider.create_resource(name, config)
            self._resources[name] = resource

            # Initialize dependencies first
            if dependencies:
                for dep_name in dependencies:
                    dep = self._resources[dep_name]
                    if dep.state != ResourceState.READY:
                        await dep.initialize()

            # Initialize resource
            await resource.initialize()
            await resource.validate()

            self._logger.info(
                "Created and initialized resource",
                extra={
                    "resource_name": name,
                    "resource_type": resource_type.value,
                },
            )
            return resource

        except Exception as e:
            # Clean up on failure
            if name in self._resources:
                del self._resources[name]
            if name in self._dependencies:
                del self._dependencies[name]
            raise StateError(f"Failed to create resource: {str(e)}") from e

    async def delete_resource(self, name: str) -> None:
        """Delete a resource.

        Args:
            name: Resource name

        Raises:
            StateError: If resource deletion fails
            ValueError: If resource doesn't exist or has dependents

        """
        resource = self._resources.get(name)
        if not resource:
            raise ValueError(f"Resource {name} not found")

        # Check for dependent resources
        dependents = [
            dep_name for dep_name, deps in self._dependencies.items() if name in deps
        ]
        if dependents:
            raise ValueError(
                f"Cannot delete resource with dependents: {', '.join(dependents)}"
            )

        if not isinstance(resource.metadata, ResourceMetadata):
            raise StateError("Invalid resource metadata type")

        provider = self._providers.get(resource.metadata.resource_type.value)
        if not provider:
            raise StateError(
                f"No provider registered for type {resource.metadata.resource_type.value}"
            )

        try:
            await resource.cleanup()
            await provider.delete_resource(name)
            del self._resources[name]
            if name in self._dependencies:
                del self._dependencies[name]

            self._logger.info(
                "Deleted resource",
                extra={
                    "resource_name": name,
                    "resource_type": resource.metadata.resource_type.value,
                },
            )

        except Exception as e:
            raise StateError(f"Failed to delete resource: {str(e)}") from e

    def get_resource(self, name: str) -> Optional[BaseResource]:
        """Get a resource by name.

        Args:
            name: Resource name

        Returns:
            Resource if found, None otherwise

        """
        return self._resources.get(name)

    def list_resources(self) -> List[BaseResource]:
        """List all managed resources.

        Returns:
            List of managed resources

        """
        return list(self._resources.values())

    def get_resources_by_type(self, resource_type: ResourceType) -> List[BaseResource]:
        """Get all resources of a specific type.

        Args:
            resource_type: Type to filter by

        Returns:
            List of resources of the specified type

        """
        return [
            r
            for r in self._resources.values()
            if isinstance(r.metadata, ResourceMetadata)
            and r.metadata.resource_type == resource_type
        ]

    def get_resources_by_state(self, state: ResourceState) -> List[BaseResource]:
        """Get all resources in a specific state.

        Args:
            state: State to filter by

        Returns:
            List of resources in the specified state

        """
        return [r for r in self._resources.values() if r.state == state]

    async def cleanup(self) -> None:
        """Clean up all resources.

        This ensures resources are cleaned up in the correct order, respecting
        their dependencies.

        Raises:
            StateError: If cleanup fails

        """
        self._logger.info("Cleaning up resource manager")

        # Clean up resources in reverse dependency order
        cleanup_order = self._get_cleanup_order()
        errors = []

        for name in cleanup_order:
            resource = self._resources.get(name)
            if resource:
                try:
                    await resource.cleanup()
                except Exception as e:
                    errors.append(f"Failed to clean up resource {name}: {e}")

        if errors:
            raise StateError("\n".join(errors))

        self._resources.clear()
        self._providers.clear()
        self._dependencies.clear()

    def _get_cleanup_order(self) -> List[str]:
        """Get resource cleanup order respecting dependencies.

        Returns:
            List of resource names in cleanup order

        """
        # Build reverse dependency graph
        reverse_deps: Dict[str, Set[str]] = {name: set() for name in self._resources}
        for name, deps in self._dependencies.items():
            for dep in deps:
                reverse_deps[dep].add(name)

        # Topological sort
        cleanup_order: List[str] = []
        visited: Set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            for dep in reverse_deps[name]:
                visit(dep)
            cleanup_order.append(name)

        for name in self._resources:
            visit(name)

        return cleanup_order
