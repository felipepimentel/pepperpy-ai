from typing import Any, Dict

from pepperpy.core.lifecycle import LifecycleManager
from pepperpy.core.resources.base import Resource
from pepperpy.core.resources.types import ResourceError
from pepperpy.core.monitoring import get_logger

logger = get_logger("resource.manager")


class ResourceManager:
    def __init__(self):
        self._resources = {}
        self._lifecycle = LifecycleManager()

    async def register_resource(self, name: str, resource: Resource) -> None:
        """Register a resource with the manager.

        Args:
            name: Resource name
            resource: Resource instance

        """
        try:
            self._resources[name] = resource
            self._lifecycle.register(resource)
            await self._lifecycle.initialize(resource.id)
            logger.info(
                "Resource registered successfully",
                resource_name=name,
                resource_id=str(resource.id),
            )
        except Exception as e:
            logger.error(
                "Failed to register resource",
                resource_name=name,
                error_message=str(e),
            )
            raise ResourceError(
                message=f"Failed to register resource {name}",
                error_type="registration_error",
                timestamp=0.0,
                details={"error": str(e)},
            )

    async def unregister_resource(self, name: str) -> None:
        """Unregister a resource from the manager.

        Args:
            name: Resource name

        """
        try:
            resource = self._resources[name]
            await self._lifecycle.terminate(resource.id)
            del self._resources[name]
            logger.info(
                "Resource unregistered successfully",
                resource_name=name,
                resource_id=str(resource.id),
            )
        except Exception as e:
            logger.error(
                "Failed to unregister resource",
                resource_name=name,
                error_message=str(e),
            )
            raise ResourceError(
                message=f"Failed to unregister resource {name}",
                error_type="unregistration_error",
                timestamp=0.0,
                details={"error": str(e)},
            )

    async def update_resource_metadata(self, name: str, metadata: Dict[str, Any]) -> None:
        """Update resource metadata.

        Args:
            name: Resource name
            metadata: Resource metadata

        """
        try:
            resource = self._resources[name]
            resource.metadata.update(metadata)
            logger.info(
                "Resource metadata updated",
                resource_name=name,
                resource_id=str(resource.id),
            )
        except Exception as e:
            logger.error(
                "Failed to update resource metadata",
                resource_name=name,
                error_message=str(e),
            )
            raise ResourceError(
                message=f"Failed to update resource metadata for {name}",
                error_type="metadata_error",
                timestamp=0.0,
                details={"error": str(e)},
            )
// ... existing code ...