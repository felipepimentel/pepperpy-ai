"""Resource provider interfaces.

This module provides the interfaces for resource providers, which are
responsible for creating and managing resources of specific types.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Sequence, TypeVar
from uuid import UUID, uuid4

from pepperpy.core.base import BaseComponent
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.logging import get_logger

from ..base import BaseResource, ResourceType
from ..base import ResourceMetadata as ResourceMetadata

logger = get_logger(__name__)

# Type variable for provider-specific resource types
ResourceT = TypeVar("ResourceT", bound=BaseResource)


class ResourceProvider(BaseComponent, Generic[ResourceT]):
    """Base class for resource providers.

    Resource providers are responsible for creating and managing resources
    of specific types. They handle resource lifecycle and ensure proper
    cleanup.

    Attributes:
        id: Unique identifier
        metadata: Provider metadata
        resource_type: Type of resources this provider manages
        resources: Dictionary of managed resources

    Example:
        >>> provider = StorageProvider()
        >>> resource = await provider.create_resource(
        ...     name="local_storage",
        ...     config={"path": "/tmp/storage"}
        ... )
        >>> assert resource.state.is_ready()

    """

    def __init__(
        self,
        resource_type: ResourceType,
        id: Optional[UUID] = None,
    ) -> None:
        """Initialize the resource provider.

        Args:
            resource_type: Type of resources this provider manages
            id: Optional provider ID

        Raises:
            ConfigurationError: If resource type is invalid

        """
        super().__init__(id or uuid4())
        self.resource_type = resource_type
        self._resources: Dict[str, ResourceT] = {}
        self._logger = logger.getChild(self.__class__.__name__)

    @abstractmethod
    async def create_resource(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> ResourceT:
        """Create a new resource.

        Args:
            name: Resource name
            config: Resource configuration

        Returns:
            The created resource

        Raises:
            ConfigurationError: If configuration is invalid
            StateError: If provider is in invalid state

        """
        raise NotImplementedError

    @abstractmethod
    async def delete_resource(
        self,
        name: str,
    ) -> None:
        """Delete a resource.

        Args:
            name: Resource name

        Raises:
            StateError: If resource is in invalid state
            ValueError: If resource does not exist

        """
        raise NotImplementedError

    async def get_resource(
        self,
        name: str,
    ) -> Optional[ResourceT]:
        """Get a resource by name.

        Args:
            name: Resource name

        Returns:
            The resource if found, None otherwise

        """
        return self._resources.get(name)

    def list_resources(self) -> Sequence[ResourceT]:
        """List all managed resources.

        Returns:
            List of managed resources

        """
        return list(self._resources.values())

    async def cleanup(self) -> None:
        """Clean up all managed resources.

        This method ensures proper cleanup of all resources managed by
        this provider.

        Raises:
            StateError: If cleanup fails

        """
        errors = []
        for name, resource in self._resources.items():
            try:
                await resource.cleanup()
            except Exception as e:
                errors.append(f"Failed to cleanup resource {name}: {e}")

        if errors:
            raise StateError("\n".join(errors))

        self._resources.clear()

    def validate(self) -> None:
        """Validate provider state.

        Raises:
            StateError: If provider state is invalid
            ConfigurationError: If configuration is invalid

        """
        super().validate()
        if not isinstance(self.resource_type, ResourceType):
            raise ConfigurationError("Invalid resource type")
        for resource in self._resources.values():
            if not isinstance(resource, BaseResource):
                raise ConfigurationError("Invalid resource instance")
