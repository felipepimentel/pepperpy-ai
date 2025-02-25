"""Resource management system.

This module provides resource management functionality:
- Resource allocation and tracking
- Resource cleanup and monitoring
- Resource metadata management
- Resource state tracking
"""

import asyncio
from typing import Any, TypeVar

from pepperpy.core.errors import ResourceError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger
from pepperpy.core.resources.base import (
    Resource,
    ResourceMetadata,
    ResourceState,
    ResourceType,
)

# Configure logging
logger = get_logger(__name__)

# Type variable for resource values
T = TypeVar("T")


class ResourceManager(LifecycleComponent):
    """Manager for resource lifecycle."""

    def __init__(self, name: str) -> None:
        """Initialize manager.

        Args:
            name: Manager name
        """
        super().__init__(name)
        self._resources: dict[str, Resource[Any]] = {}
        self._metadata: dict[str, ResourceMetadata] = {}
        self._lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """Initialize manager.

        Raises:
            ResourceError: If initialization fails
        """
        logger.info("Resource manager initialized", extra={"name": self.name})

    async def _cleanup(self) -> None:
        """Clean up manager.

        Raises:
            ResourceError: If cleanup fails
        """
        async with self._lock:
            for resource in self._resources.values():
                try:
                    await resource.cleanup()
                except Exception as e:
                    logger.error(
                        "Failed to clean up resource",
                        extra={
                            "resource": resource.name,
                            "error": str(e),
                        },
                    )
            self._resources.clear()
            self._metadata.clear()
        logger.info("Resource manager cleaned up", extra={"name": self.name})

    async def allocate_resource(
        self,
        id: str,
        type: ResourceType,
        value: T,
        metadata: dict[str, Any] | None = None,
    ) -> Resource[T]:
        """Allocate a resource.

        Args:
            id: Resource ID
            type: Resource type
            value: Resource value
            metadata: Optional resource metadata

        Returns:
            Resource[T]: Allocated resource

        Raises:
            ResourceError: If allocation fails
        """
        try:
            if id in self._resources:
                raise ResourceError(f"Resource {id} already exists")

            resource = Resource(id, type, value)
            await resource.initialize()

            self._resources[id] = resource
            self._metadata[id] = ResourceMetadata(
                type=type,
                metadata=metadata or {},
            )

            logger.info(
                "Resource allocated",
                extra={
                    "id": id,
                    "type": type,
                },
            )

            return resource

        except Exception as e:
            raise ResourceError(f"Failed to allocate resource {id}: {e}")

    async def deallocate_resource(self, id: str) -> None:
        """Deallocate a resource.

        Args:
            id: Resource ID

        Raises:
            ResourceError: If deallocation fails
        """
        try:
            if id not in self._resources:
                raise ResourceError(f"Resource {id} not found")

            resource = self._resources[id]
            await resource.cleanup()

            del self._resources[id]
            del self._metadata[id]

            logger.info(
                "Resource deallocated",
                extra={
                    "id": id,
                    "type": resource.type,
                },
            )

        except Exception as e:
            raise ResourceError(f"Failed to deallocate resource {id}: {e}")

    def get_resource(self, id: str) -> Resource[Any] | None:
        """Get a resource.

        Args:
            id: Resource ID

        Returns:
            Resource | None: Resource if found, None otherwise
        """
        return self._resources.get(id)

    def get_metadata(self, id: str) -> ResourceMetadata | None:
        """Get resource metadata.

        Args:
            id: Resource ID

        Returns:
            ResourceMetadata | None: Resource metadata if found, None otherwise
        """
        return self._metadata.get(id)

    def list_resources(
        self,
        type: ResourceType | None = None,
        state: ResourceState | None = None,
    ) -> list[Resource[Any]]:
        """List resources.

        Args:
            type: Optional resource type filter
            state: Optional resource state filter

        Returns:
            list[Resource]: List of matching resources
        """
        resources = list(self._resources.values())

        if type is not None:
            resources = [r for r in resources if r.type == type]

        if state is not None:
            resources = [r for r in resources if r.state == state]

        return resources

    def get_stats(self) -> dict[str, Any]:
        """Get resource statistics.

        Returns:
            dict[str, Any]: Resource statistics
        """
        stats: dict[str, Any] = {
            "total": len(self._resources),
            "by_type": {},
            "by_state": {},
        }

        for resource in self._resources.values():
            # Count by type
            type_str = str(resource.type)
            stats["by_type"][type_str] = stats["by_type"].get(type_str, 0) + 1

            # Count by state
            state_str = str(resource.state)
            stats["by_state"][state_str] = stats["by_state"].get(state_str, 0) + 1

        return stats


# Global resource manager instance
resource_manager = ResourceManager("global")


# Export public API
__all__ = [
    "ResourceManager",
    "resource_manager",
]
