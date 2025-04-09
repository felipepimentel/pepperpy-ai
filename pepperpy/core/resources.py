"""
Resource management for PepperPy core.

This module provides consistent resource management capabilities for all providers.
"""

import asyncio
import enum
import threading
from typing import Any

from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class ResourceError(PepperpyError):
    """Base exception for resource-related errors."""


class ResourceType(str, enum.Enum):
    """Types of resources that can be managed."""

    CONNECTION = "connection"
    CLIENT = "client"
    SESSION = "session"
    MODEL = "model"
    DATABASE = "database"
    FILE = "file"
    CACHE = "cache"
    TOKEN = "token"
    PROCESS = "process"
    SERVICE = "service"
    CUSTOM = "custom"


# Global resource registry
# Structure: {resource_type: {resource_id: (resource, owner_id)}}
_resource_registry: dict[str, dict[str, tuple[Any, str]]] = {}

# Registry lock to ensure thread safety
_registry_lock = threading.RLock()

# Keep track of owners and their resources
# Structure: {owner_id: {(resource_type, resource_id), ...}}
_owner_resources: dict[str, set[tuple[str, str]]] = {}


def register_resource(
    resource_type: str, resource_id: str, resource: Any, owner_id: str
) -> None:
    """Register a resource.

    Args:
        resource_type: Type of resource
        resource_id: Resource identifier
        resource: Resource object
        owner_id: ID of the owner

    Raises:
        ResourceError: If resource with same ID already exists
    """
    with _registry_lock:
        # Ensure resource type dictionary exists
        if resource_type not in _resource_registry:
            _resource_registry[resource_type] = {}

        # Check if resource ID already exists
        if resource_id in _resource_registry[resource_type]:
            existing_resource, existing_owner = _resource_registry[resource_type][
                resource_id
            ]
            if existing_owner != owner_id:
                raise ResourceError(
                    f"Resource {resource_type}.{resource_id} already exists with different owner"
                )

        # Register the resource
        _resource_registry[resource_type][resource_id] = (resource, owner_id)

        # Track resource for owner
        if owner_id not in _owner_resources:
            _owner_resources[owner_id] = set()
        _owner_resources[owner_id].add((resource_type, resource_id))

        logger.debug(
            f"Registered resource {resource_type}.{resource_id} for owner {owner_id}"
        )


def unregister_resource(resource_type: str, resource_id: str) -> None:
    """Unregister a resource.

    Args:
        resource_type: Type of resource
        resource_id: Resource identifier
    """
    with _registry_lock:
        # Check if resource exists
        if (
            resource_type in _resource_registry
            and resource_id in _resource_registry[resource_type]
        ):
            resource, owner_id = _resource_registry[resource_type][resource_id]

            # Remove from registry
            del _resource_registry[resource_type][resource_id]

            # If resource type dictionary is empty, remove it
            if not _resource_registry[resource_type]:
                del _resource_registry[resource_type]

            # Remove from owner tracking
            if owner_id in _owner_resources:
                _owner_resources[owner_id].discard((resource_type, resource_id))

                # If owner has no more resources, remove from tracking
                if not _owner_resources[owner_id]:
                    del _owner_resources[owner_id]

            logger.debug(f"Unregistered resource {resource_type}.{resource_id}")


def get_resource(resource_type: str, resource_id: str) -> Any | None:
    """Get a registered resource.

    Args:
        resource_type: Type of resource
        resource_id: Resource identifier

    Returns:
        Resource object or None if not found
    """
    with _registry_lock:
        if (
            resource_type in _resource_registry
            and resource_id in _resource_registry[resource_type]
        ):
            resource, _ = _resource_registry[resource_type][resource_id]
            return resource
    return None


def get_owner_resources(owner_id: str) -> dict[str, dict[str, Any]]:
    """Get all resources owned by a specific owner.

    Args:
        owner_id: ID of the owner

    Returns:
        Dictionary of resources by type and ID
    """
    result: dict[str, dict[str, Any]] = {}

    with _registry_lock:
        if owner_id in _owner_resources:
            for resource_type, resource_id in _owner_resources[owner_id]:
                if resource_type not in result:
                    result[resource_type] = {}

                if (
                    resource_type in _resource_registry
                    and resource_id in _resource_registry[resource_type]
                ):
                    resource, _ = _resource_registry[resource_type][resource_id]
                    result[resource_type][resource_id] = resource

    return result


async def cleanup_resource(resource: Any, resource_type: str, resource_id: str) -> None:
    """Clean up a resource.

    Args:
        resource: Resource object
        resource_type: Type of resource
        resource_id: Resource identifier
    """
    try:
        # Try different cleanup methods depending on resource
        if hasattr(resource, "cleanup") and callable(resource.cleanup):
            if asyncio.iscoroutinefunction(resource.cleanup):
                await resource.cleanup()
            else:
                resource.cleanup()
        elif hasattr(resource, "close") and callable(resource.close):
            if asyncio.iscoroutinefunction(resource.close):
                await resource.close()
            else:
                resource.close()
        elif hasattr(resource, "__aexit__") and callable(resource.__aexit__):
            await resource.__aexit__(None, None, None)
        elif hasattr(resource, "__exit__") and callable(resource.__exit__):
            resource.__exit__(None, None, None)

        logger.debug(f"Cleaned up resource {resource_type}.{resource_id}")
    except Exception as e:
        logger.warning(f"Error cleaning up resource {resource_type}.{resource_id}: {e}")


async def cleanup_owner_resources(owner_id: str) -> None:
    """Clean up all resources owned by a specific owner.

    Args:
        owner_id: ID of the owner
    """
    # Get all resources for this owner
    resources = get_owner_resources(owner_id)

    # Clean up each resource
    for resource_type, resources_by_id in resources.items():
        for resource_id, resource in resources_by_id.items():
            await cleanup_resource(resource, resource_type, resource_id)
            unregister_resource(resource_type, resource_id)

    logger.debug(f"Cleaned up all resources for owner {owner_id}")


class ResourceManager:
    """Resource manager for providers.

    This class provides a convenient interface for managing resources.
    """

    def __init__(self, owner_id: str) -> None:
        """Initialize resource manager.

        Args:
            owner_id: ID of the owner
        """
        self.owner_id = owner_id

    def register(self, resource_type: str, resource_id: str, resource: Any) -> None:
        """Register a resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            resource: Resource object

        Raises:
            ResourceError: If resource with same ID already exists
        """
        register_resource(resource_type, resource_id, resource, self.owner_id)

    def unregister(self, resource_type: str, resource_id: str) -> None:
        """Unregister a resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
        """
        unregister_resource(resource_type, resource_id)

    def get(self, resource_type: str, resource_id: str) -> Any | None:
        """Get a registered resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier

        Returns:
            Resource object or None if not found
        """
        return get_resource(resource_type, resource_id)

    def get_all(self) -> dict[str, dict[str, Any]]:
        """Get all resources owned by this manager.

        Returns:
            Dictionary of resources by type and ID
        """
        return get_owner_resources(self.owner_id)

    async def cleanup(self) -> None:
        """Clean up all resources owned by this manager."""
        await cleanup_owner_resources(self.owner_id)

    async def cleanup_resource(self, resource_type: str, resource_id: str) -> None:
        """Clean up a specific resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
        """
        resource = self.get(resource_type, resource_id)
        if resource:
            await cleanup_resource(resource, resource_type, resource_id)
            self.unregister(resource_type, resource_id)
