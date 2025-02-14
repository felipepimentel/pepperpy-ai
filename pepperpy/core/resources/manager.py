"""Resource manager implementation."""

import asyncio
from typing import Any, Dict, List, Optional, Type

from pepperpy.core.lifecycle import Lifecycle, LifecycleManager
from pepperpy.core.monitoring import LoggerFactory
from pepperpy.core.monitoring.metrics import Counter, Gauge, Histogram, MetricType

from .base import Resource
from .types import ResourceConfig, ResourceState


class ResourceManager(Lifecycle):
    """Manages the lifecycle of resources."""

    def __init__(self):
        """Initialize the resource manager."""
        super().__init__()
        self._resources: Dict[str, Resource] = {}
        self._lifecycle = LifecycleManager()
        self._logger = LoggerFactory().get_logger(
            name="resource.manager",
            context={"component": "ResourceManager"},
        )

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
        """Clean up all resources and shut down the manager."""
        self._logger.info("Cleaning up resource manager")
        cleanup_tasks = [
            self._cleanup_resource(name) for name in list(self._resources.keys())
        ]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        await self._lifecycle.terminate(self.id)

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
