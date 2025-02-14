"""Resource pooling and allocation."""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.monitoring import LoggerFactory
from pepperpy.core.monitoring.metrics import Counter, Gauge, MetricType

from .base import Resource
from .manager import ResourceManager
from .types import ResourceConfig, ResourceState, ResourceType


@dataclass
class ResourceAllocation:
    """Resource allocation information."""

    resource: Resource
    owner_id: str
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    metadata: Dict[str, str] = field(default_factory=dict)


class ResourcePool(Lifecycle):
    """Manages a pool of resources for allocation."""

    def __init__(self, resource_type: ResourceType, manager: ResourceManager):
        """Initialize the resource pool.

        Args:
            resource_type: Type of resources in this pool
            manager: Resource manager instance

        """
        super().__init__()
        self.resource_type = resource_type
        self._manager = manager
        self._available: Set[str] = set()
        self._allocated: Dict[str, ResourceAllocation] = {}
        self._logger = LoggerFactory().get_logger(
            name=f"resource.pool.{resource_type.value}"
        )

        # Initialize metrics
        self._available_resources = Gauge(
            name=f"resource_pool_available_{resource_type.value}",
            type=MetricType.GAUGE,
            description=f"Number of available {resource_type.value} resources",
        )
        self._allocated_resources = Gauge(
            name=f"resource_pool_allocated_{resource_type.value}",
            type=MetricType.GAUGE,
            description=f"Number of allocated {resource_type.value} resources",
        )
        self._allocation_requests = Counter(
            name=f"resource_pool_allocations_{resource_type.value}",
            type=MetricType.COUNTER,
            description=f"Number of {resource_type.value} resource allocation requests",
        )

    async def add_resource(self, name: str, config: ResourceConfig) -> Resource:
        """Add a resource to the pool.

        Args:
            name: Resource name
            config: Resource configuration

        Returns:
            The added resource

        Raises:
            ValueError: If resource type doesn't match pool type

        """
        if config.type != self.resource_type:
            raise ValueError(
                f"Resource type {config.type} doesn't match pool type {self.resource_type}"
            )

        resource = await self._manager.register(name, config)
        self._available.add(name)
        self._available_resources.inc()
        self._logger.info(f"Added resource {name} to pool")
        return resource

    async def allocate(
        self, owner_id: str, metadata: Optional[Dict[str, str]] = None
    ) -> Optional[Resource]:
        """Allocate a resource from the pool.

        Args:
            owner_id: ID of the resource owner
            metadata: Optional allocation metadata

        Returns:
            Allocated resource or None if none available

        """
        self._allocation_requests.inc()

        if not self._available:
            self._logger.warning("No resources available for allocation")
            return None

        resource_name = next(iter(self._available))
        resource = await self._manager.get(resource_name)
        if not resource:
            self._logger.error(f"Resource {resource_name} not found")
            return None

        self._available.remove(resource_name)
        self._allocated[resource_name] = ResourceAllocation(
            resource=resource,
            owner_id=owner_id,
            metadata=metadata or {},
        )

        self._available_resources.dec()
        self._allocated_resources.inc()
        self._logger.info(
            f"Allocated resource {resource_name}",
            context={"owner_id": owner_id},
        )
        return resource

    async def release(self, resource_name: str) -> None:
        """Release an allocated resource.

        Args:
            resource_name: Name of the resource to release

        Raises:
            ValueError: If resource is not allocated

        """
        if resource_name not in self._allocated:
            raise ValueError(f"Resource {resource_name} is not allocated")

        allocation = self._allocated.pop(resource_name)
        self._available.add(resource_name)
        self._available_resources.inc()
        self._allocated_resources.dec()
        self._logger.info(
            f"Released resource {resource_name}",
            context={"owner_id": allocation.owner_id},
        )

    async def initialize(self) -> None:
        """Initialize the resource pool."""
        self._logger.info(f"Initializing {self.resource_type.value} resource pool")
        # Find existing resources of this type
        resources = self._manager.get_resources_by_type(self.resource_type.value)
        for resource in resources:
            if resource.state == ResourceState.READY:
                self._available.add(resource.name)
                self._available_resources.inc()

    async def cleanup(self) -> None:
        """Clean up the resource pool."""
        self._logger.info(f"Cleaning up {self.resource_type.value} resource pool")
        # Release all allocated resources
        for name in list(self._allocated.keys()):
            await self.release(name)

    def get_allocation(self, resource_name: str) -> Optional[ResourceAllocation]:
        """Get allocation information for a resource.

        Args:
            resource_name: Name of the resource

        Returns:
            Allocation information if resource is allocated

        """
        return self._allocated.get(resource_name)

    async def list_available(self) -> List[Resource]:
        """List available resources.

        Returns:
            List of available resources

        """
        available_resources: List[Resource] = []
        for name in self._available:
            if resource := await self._manager.get(name):
                available_resources.append(resource)
        return available_resources

    def list_allocated(self) -> List[ResourceAllocation]:
        """List allocated resources.

        Returns:
            List of resource allocations

        """
        return list(self._allocated.values())
