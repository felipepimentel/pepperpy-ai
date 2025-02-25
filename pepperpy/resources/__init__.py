"""Resources module for the Pepperpy framework.

This module provides functionality for managing AI resources:
- Base resource interface
- Resource configuration
- Common resource types
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from pepperpy.core.extensions import Extension
from pepperpy.core.extensions import ExtensionMetadata as ExtensionMetadata
from pepperpy.core.events import EventBus


class ResourceType(Enum):
    """Types of resources."""

    MEMORY = auto()
    STORAGE = auto()
    DATABASE = auto()
    NETWORK = auto()
    FILE = auto()
    API = auto()


class ResourceMetadata(BaseModel):
    """Metadata for resources.

    Attributes:
        resource_type: Type of resource
        resource_name: Name of the resource
        version: Version of the resource
        tags: Resource tags
        properties: Additional properties
    """

    resource_type: ResourceType
    resource_name: str
    version: str
    tags: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)


class BaseResource(Extension):
    """Base class for AI resources.

    This class defines the interface that all resources must implement.
    """

    def __init__(
        self,
        metadata: ResourceMetadata,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize resource.

        Args:
            metadata: Resource metadata
            event_bus: Optional event bus for resource events
        """
        super().__init__(
            name=metadata.resource_name,
            version=metadata.version,
            event_bus=event_bus,
        )
        self._resource_metadata = metadata

    @property
    def resource_metadata(self) -> ResourceMetadata:
        """Get resource metadata.

        Returns:
            Resource metadata
        """
        return self._resource_metadata

    async def _initialize(self) -> None:
        """Initialize resource."""
        pass

    async def _cleanup(self) -> None:
        """Clean up resource."""
        pass

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute resource operation.

        Args:
            operation: Operation to execute
            params: Operation parameters

        Returns:
            Operation result

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Resource must implement execute method")


class MemoryResource(BaseResource):
    """Base class for memory resources."""

    def __init__(
        self,
        metadata: ResourceMetadata,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize memory resource.

        Args:
            metadata: Resource metadata
            event_bus: Optional event bus for resource events
        """
        if metadata.resource_type != ResourceType.MEMORY:
            raise ValueError("Resource type must be MEMORY")
        super().__init__(metadata, event_bus)


class StorageResource(BaseResource):
    """Base class for storage resources."""

    def __init__(
        self,
        metadata: ResourceMetadata,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize storage resource.

        Args:
            metadata: Resource metadata
            event_bus: Optional event bus for resource events
        """
        if metadata.resource_type != ResourceType.STORAGE:
            raise ValueError("Resource type must be STORAGE")
        super().__init__(metadata, event_bus)


class ResourceManager(Extension):
    """Manager for AI resources.

    This class provides functionality for managing resources:
    - Resource registration and discovery
    - Resource lifecycle management
    - Resource dependency resolution
    """

    def __init__(
        self,
        name: str = "resource_manager",
        version: str = "1.0.0",
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize resource manager.

        Args:
            name: Manager name
            version: Manager version
            event_bus: Optional event bus for manager events
        """
        super().__init__(name=name, version=version, event_bus=event_bus)
        self._resources: Dict[str, BaseResource] = {}

    async def register_resource(self, resource: BaseResource) -> None:
        """Register a resource.

        Args:
            resource: Resource to register
        """
        self._resources[str(resource.metadata.id)] = resource

    async def unregister_resource(self, resource_id: str) -> None:
        """Unregister a resource.

        Args:
            resource_id: ID of the resource to unregister
        """
        if resource_id in self._resources:
            del self._resources[resource_id]

    async def get_resource(self, resource_id: str) -> Optional[BaseResource]:
        """Get a resource by ID.

        Args:
            resource_id: ID of the resource to get

        Returns:
            Resource if found, None otherwise
        """
        return self._resources.get(resource_id)

    async def get_resources(self) -> List[BaseResource]:
        """Get all registered resources.

        Returns:
            List of registered resources
        """
        return list(self._resources.values())

    async def _initialize(self) -> None:
        """Initialize all registered resources."""
        for resource in self._resources.values():
            await resource.initialize()

    async def _cleanup(self) -> None:
        """Clean up all registered resources."""
        for resource in self._resources.values():
            await resource.cleanup()
        self._resources.clear()
