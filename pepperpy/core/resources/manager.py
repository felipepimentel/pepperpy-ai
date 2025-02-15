"""Resource manager implementation.

This module provides the central resource manager that handles resource lifecycle,
dependencies, and state management.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set

from pepperpy.core.lifecycle import Lifecycle, LifecycleManager
from pepperpy.core.monitoring.logging import get_logger
from pepperpy.core.monitoring.metrics import Counter, Gauge, Histogram, MetricType

from .base import Resource, ResourceConfig, ResourceError, ResourceProvider
from .types import ResourceState


class ResourceManager(Lifecycle):
    """Central manager for resource lifecycle and dependencies.

    This class provides a unified interface for creating, managing, and cleaning up
    resources, handling their dependencies and ensuring proper initialization order.
    """

    def __init__(self) -> None:
        """Initialize the resource manager."""
        super().__init__()
        self._resources: Dict[str, Resource] = {}
        self._providers: Dict[str, ResourceProvider] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._lifecycle = LifecycleManager()
        self._logger = get_logger(__name__)

        # Initialize metrics
        self._total_resources = Counter(
            name="resource_total",
            type=MetricType.COUNTER,
            description="Total number of resources",
        )
        self._resource_states = Gauge(
            name="resource_states",
            type=MetricType.GAUGE,
            description="Number of resources in each state",
        )
        self._resource_init_time = Histogram(
            name="resource_init_time",
            type=MetricType.HISTOGRAM,
            description="Time taken to initialize resources",
        )
        self._resource_cleanup_time = Histogram(
            name="resource_cleanup_time",
            type=MetricType.HISTOGRAM,
            description="Time taken to cleanup resources",
        )

    async def register(
        self,
        name: str,
        config: ResourceConfig,
        resource_class: Optional[Type[Resource]] = None,
    ) -> Resource:
        """Register and initialize a resource.

        Args:
            name: The name of the resource.
            config: The resource configuration.
            resource_class: Optional specific resource class to use.

        Returns:
            The initialized resource.

        Raises:
            ValueError: If a resource with the same name already exists.

        """
        if name in self._resources:
            raise ValueError(f"Resource {name} already exists")

        resource_class = resource_class or Resource
        resource = resource_class(name, config)
        await self._lifecycle.initialize(resource.id)
        self._resources[name] = resource

        try:
            start_time = asyncio.get_event_loop().time()
            await resource.initialize()
            init_time = asyncio.get_event_loop().time() - start_time

            # Update metrics
            self._total_resources.inc()
            self._resource_states.inc()
            self._resource_init_time.observe(value=init_time)

            self._logger.info(
                "Resource registered successfully",
                context={"name": name, "type": config.type.value},
            )
            return resource
        except Exception as e:
            await self._cleanup_resource(name)
            self._logger.error(
                "Failed to register resource",
                context={"name": name},
                error=e,
            )
            raise

    async def get(self, name: str) -> Optional[Resource]:
        """Get a registered resource by name.

        Args:
            name: The name of the resource.

        Returns:
            The resource if found, None otherwise.

        """
        return self._resources.get(name)

    async def list(self) -> List[Resource]:
        """List all registered resources.

        Returns:
            List of registered resources.

        """
        return list(self._resources.values())

    async def unregister(self, name: str) -> None:
        """Unregister and cleanup a resource.

        Args:
            name: The name of the resource.

        Raises:
            ValueError: If the resource does not exist.

        """
        if name not in self._resources:
            raise ValueError(f"Resource {name} does not exist")

        await self._cleanup_resource(name)
        self._logger.info(
            "Resource unregistered successfully",
            context={"name": name},
        )

    async def _cleanup_resource(self, name: str) -> None:
        """Clean up a resource and remove it from management.

        Args:
            name: The name of the resource.

        """
        resource = self._resources.pop(name, None)
        if resource:
            try:
                start_time = asyncio.get_event_loop().time()
                await resource.cleanup()
                cleanup_time = asyncio.get_event_loop().time() - start_time

                # Update metrics
                self._total_resources.reset()  # Reset counter since we can't decrement
                self._resource_states.dec()
                self._resource_cleanup_time.observe(value=cleanup_time)

            except Exception as e:
                self._logger.error(
                    "Error cleaning up resource",
                    context={"name": name},
                    error=e,
                )
            await self._lifecycle.terminate(resource.id)

    async def initialize(self) -> None:
        """Initialize the resource manager."""
        self._logger.info("Initializing resource manager")
        await self._lifecycle.initialize(self.id)

    async def cleanup(self) -> None:
        """Clean up all resources.

        This ensures resources are cleaned up in the correct order, respecting
        their dependencies.
        """
        self._logger.info("Cleaning up resource manager")

        # Clean up resources in reverse dependency order
        for name in self._get_cleanup_order():
            resource = self._resources.get(name)
            if resource:
                try:
                    await resource.cleanup()
                except Exception as e:
                    self._logger.error(
                        "Failed to clean up resource",
                        resource_name=name,
                        error=str(e),
                    )

        self._resources.clear()
        self._providers.clear()
        self._dependencies.clear()

    def get_resources_by_state(self, state: ResourceState) -> List[Resource]:
        """Get all resources in a specific state.

        Args:
            state: The state to filter by.

        Returns:
            List of resources in the specified state.

        """
        return [r for r in self._resources.values() if r.state == state]

    def get_resources_by_type(self, resource_type: str) -> List[Resource]:
        """Get all resources of a specific type.

        Args:
            resource_type: The type to filter by.

        Returns:
            List of resources of the specified type.

        """
        return [
            r for r in self._resources.values() if r.config.type.value == resource_type
        ]

    async def update_metadata(self, name: str, metadata: Dict[str, Any]) -> None:
        """Update the metadata of a resource.

        Args:
            name: The name of the resource.
            metadata: The metadata to update.

        Raises:
            ValueError: If the resource does not exist.

        """
        resource = await self.get(name)
        if not resource:
            raise ValueError(f"Resource {name} does not exist")

        resource._metadata.update(metadata)
        self._logger.info(
            "Resource metadata updated",
            context={"name": name, "metadata": metadata},
        )

    def update_resource_metrics(self) -> None:
        """Update resource state metrics."""
        # Reset state metrics for each resource type and state
        for resource_type in {r.config.type.value for r in self._resources.values()}:
            for state in ResourceState:
                self._resource_states.set(0)

        # Update current state counts
        for resource in self._resources.values():
            self._resource_states.inc()

    def register_provider(
        self,
        provider_type: str,
        provider: ResourceProvider,
    ) -> None:
        """Register a resource provider.

        Args:
            provider_type: Type of resources this provider handles
            provider: Provider instance

        Raises:
            ValueError: If provider type is already registered

        """
        if provider_type in self._providers:
            raise ValueError(f"Provider for type {provider_type} already registered")

        self._providers[provider_type] = provider
        self._logger.info(
            "Registered resource provider",
            provider_type=provider_type,
        )

    async def create_resource(
        self,
        name: str,
        config: ResourceConfig,
        dependencies: Optional[List[str]] = None,
    ) -> Resource:
        """Create and initialize a resource.

        Args:
            name: Resource name
            config: Resource configuration
            dependencies: Optional list of resource dependencies

        Returns:
            Created and initialized resource

        Raises:
            ResourceError: If resource creation fails
            ValueError: If resource name already exists

        """
        if name in self._resources:
            raise ValueError(f"Resource {name} already exists")

        provider = self._providers.get(config.type.value)
        if not provider:
            raise ResourceError(
                f"No provider registered for type {config.type.value}",
                config.type,
                name,
            )

        # Record dependencies
        if dependencies:
            missing = [d for d in dependencies if d not in self._resources]
            if missing:
                raise ResourceError(
                    f"Dependencies not found: {', '.join(missing)}",
                    config.type,
                    name,
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
                    if not dep.is_initialized:
                        await dep.initialize()

            # Initialize resource
            await resource.initialize()
            await resource.validate()

            self._logger.info(
                "Created and initialized resource",
                resource_name=name,
                resource_type=config.type.value,
            )
            return resource

        except Exception as e:
            # Clean up on failure
            if name in self._resources:
                del self._resources[name]
            if name in self._dependencies:
                del self._dependencies[name]
            raise ResourceError(
                f"Failed to create resource: {str(e)}",
                config.type,
                name,
            ) from e

    async def delete_resource(self, name: str) -> None:
        """Delete a resource.

        Args:
            name: Resource name

        Raises:
            ResourceError: If resource deletion fails
            ValueError: If resource doesn't exist or has dependents

        """
        resource = self._resources.get(name)
        if not resource:
            raise ValueError(f"Resource {name} not found")

        # Check for dependent resources
        dependents = self._get_dependents(name)
        if dependents:
            raise ValueError(
                f"Cannot delete resource with dependents: {', '.join(dependents)}"
            )

        provider = self._providers.get(resource.config.type.value)
        if not provider:
            raise ResourceError(
                f"No provider registered for type {resource.config.type.value}",
                resource.config.type,
                name,
            )

        try:
            await resource.cleanup()
            await provider.delete_resource(resource)
            del self._resources[name]
            if name in self._dependencies:
                del self._dependencies[name]

            self._logger.info(
                "Deleted resource",
                resource_name=name,
                resource_type=resource.config.type.value,
            )

        except Exception as e:
            raise ResourceError(
                f"Failed to delete resource: {str(e)}",
                resource.config.type,
                name,
            ) from e

    def get_resource(self, name: str) -> Optional[Resource]:
        """Get a resource by name.

        Args:
            name: Resource name

        Returns:
            Resource if found, None otherwise

        """
        return self._resources.get(name)

    def _get_dependents(self, name: str) -> Set[str]:
        """Get resources that depend on the given resource.

        Args:
            name: Resource name

        Returns:
            Set of dependent resource names

        """
        return {
            res_name for res_name, deps in self._dependencies.items() if name in deps
        }

    def _get_cleanup_order(self) -> List[str]:
        """Get resource names in dependency-aware cleanup order.

        Returns:
            List of resource names in cleanup order

        """
        visited: Set[str] = set()
        order: List[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            for dependent in self._get_dependents(name):
                visit(dependent)
            order.append(name)

        for name in self._resources:
            visit(name)

        return order


# Global resource manager instance
resource_manager = ResourceManager()
