"""Resource manager system.

This module provides resource management functionality:
- Resource allocation
- Resource tracking
- Resource cleanup
- Resource monitoring
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

    async def initialize(self) -> None:
        """Initialize manager.

        Raises:
            ResourceError: If initialization fails
        """
        try:
            await super().initialize()
            logger.info("Resource manager initialized", extra={"name": self.name})
        except Exception as e:
            raise ResourceError(f"Failed to initialize resource manager: {e}")

    async def cleanup(self) -> None:
        """Clean up manager.

        Raises:
            ResourceError: If cleanup fails
        """
        try:
            await super().cleanup()
            async with self._lock:
                for resource in self._resources.values():
                    try:
                        await resource.cleanup()
                    except Exception as e:
                        logger.error(
                            "Failed to clean up resource",
                            extra={
                                "resource": resource.id,
                                "error": str(e),
                            },
                        )
                self._resources.clear()
                self._metadata.clear()
            logger.info("Resource manager cleaned up", extra={"name": self.name})
        except Exception as e:
            raise ResourceError(f"Failed to clean up resource manager: {e}")

    async def allocate_resource(
        self,
        id: str,
        type: ResourceType,
        value: T,
        metadata: dict[str, Any] | None = None,
    ) -> Resource[T]:
        """Allocate resource.

        Args:
            id: Resource identifier
            type: Resource type
            value: Resource value
            metadata: Optional resource metadata

        Returns:
            Allocated resource

        Raises:
            ResourceError: If allocation fails
        """
        try:
            async with self._lock:
                if id in self._resources:
                    raise ResourceError(f"Resource already exists: {id}")

                # Create resource
                resource = Resource(
                    id=id,
                    type=type,
                    value=value,
                    state=ResourceState.ALLOCATED,
                )

                # Store metadata
                self._metadata[id] = ResourceMetadata(
                    type=type,
                    metadata=metadata or {},
                )

                # Initialize resource
                await resource.initialize()
                self._resources[id] = resource

                logger.info(
                    "Allocated resource",
                    extra={
                        "id": id,
                        "type": type,
                    },
                )

                return resource

        except Exception as e:
            raise ResourceError(f"Failed to allocate resource: {e}")

    async def deallocate_resource(self, id: str) -> None:
        """Deallocate resource.

        Args:
            id: Resource identifier

        Raises:
            ResourceError: If deallocation fails
        """
        try:
            async with self._lock:
                resource = self._resources.get(id)
                if not resource:
                    raise ResourceError(f"Resource not found: {id}")

                # Clean up resource
                await resource.cleanup()

                # Remove resource
                del self._resources[id]
                self._metadata.pop(id, None)

                logger.info("Deallocated resource", extra={"id": id})

        except Exception as e:
            raise ResourceError(f"Failed to deallocate resource: {e}")

    def get_resource(self, id: str) -> Resource[Any] | None:
        """Get resource instance.

        Args:
            id: Resource identifier

        Returns:
            Resource instance if found
        """
        return self._resources.get(id)

    def get_metadata(self, id: str) -> ResourceMetadata | None:
        """Get resource metadata.

        Args:
            id: Resource identifier

        Returns:
            Resource metadata if found
        """
        return self._metadata.get(id)

    def list_resources(
        self,
        type: ResourceType | None = None,
        state: ResourceState | None = None,
    ) -> list[Resource[Any]]:
        """List allocated resources.

        Args:
            type: Optional resource type filter
            state: Optional resource state filter

        Returns:
            List of resources
        """
        resources = list(self._resources.values())

        if type:
            resources = [r for r in resources if r.type == type]
        if state:
            resources = [r for r in resources if r.state == state]

        return resources

    def get_stats(self) -> dict[str, Any]:
        """Get resource statistics.

        Returns:
            Resource statistics
        """
        stats: dict[str, Any] = {
            "total_resources": len(self._resources),
            "by_type": {},
            "by_state": {},
        }

        # Count by type
        for resource in self._resources.values():
            if resource.type not in stats["by_type"]:
                stats["by_type"][resource.type] = 0
            stats["by_type"][resource.type] += 1

            if resource.state not in stats["by_state"]:
                stats["by_state"][resource.state] = 0
            stats["by_state"][resource.state] += 1

        return stats


# Global resource manager instance
resource_manager = ResourceManager("global")


# Export public API
__all__ = [
    "ResourceManager",
    "resource_manager",
]
