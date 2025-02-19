"""Resource management for the Pepperpy framework.

This module provides a unified interface for managing different types of
resources like storage, compute, and network resources.

Example:
    >>> from pepperpy.resources import StorageResource, ResourceMetadata, ResourceType
    >>> resource = StorageResource(
    ...     metadata=ResourceMetadata(
    ...         resource_type=ResourceType.STORAGE,
    ...         resource_name="local_storage",
    ...     )
    ... )
    >>> await resource.initialize()
    >>> assert resource.state.is_ready()

"""

from .base import (
    BaseResource,
    ResourceMetadata,
    ResourceResult,
    ResourceState,
    ResourceType,
)
from .manager import ResourceManager
from .providers import ResourceProvider

# Common resource types
from .types import (
    ComputeResource,
    MemoryResource,
    ModelResource,
    NetworkResource,
    ServiceResource,
    StorageResource,
)

__all__ = [
    # Base types
    "BaseResource",
    "ResourceMetadata",
    "ResourceResult",
    "ResourceState",
    "ResourceType",
    # Manager
    "ResourceManager",
    # Providers
    "ResourceProvider",
    # Resource types
    "ComputeResource",
    "MemoryResource",
    "ModelResource",
    "NetworkResource",
    "ServiceResource",
    "StorageResource",
]
