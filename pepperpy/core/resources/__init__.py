"""Resource management system.

This module provides resource management functionality:
- Resource definition and lifecycle
- Resource tracking and monitoring
- Resource allocation and deallocation
- Resource metadata and state management
"""

from pepperpy.core.resources.base import (
    FileResource,
    MemoryResource,
    NetworkResource,
    Resource,
    ResourceMetadata,
    ResourceState,
    ResourceType,
)
from pepperpy.core.resources.manager import ResourceManager

# Export public API
__all__ = [
    "FileResource",
    "MemoryResource",
    "NetworkResource",
    "Resource",
    "ResourceManager",
    "ResourceMetadata",
    "ResourceState",
    "ResourceType",
]
