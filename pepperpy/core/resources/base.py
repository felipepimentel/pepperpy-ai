"""Base interfaces and types for resource management.

This module provides the core interfaces and types for managing resources in a
unified way, with support for lifecycle management and configuration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.monitoring.logging import get_logger

from .types import ResourceConfig, ResourceError, ResourceOperationError, ResourceState

if TYPE_CHECKING:
    from .base import Resource


class ResourceType(Enum):
    """Types of resources supported by the system."""

    STORAGE = "storage"  # File systems, databases, caches
    COMPUTE = "compute"  # Processing units, workers
    NETWORK = "network"  # Network connections, APIs
    MEMORY = "memory"  # Memory caches, buffers
    MODEL = "model"  # AI models, embeddings
    SERVICE = "service"  # External services


@dataclass
class ResourceConfig:
    """Configuration for a resource.

    This class defines the configuration parameters for a resource, including
    its type, settings, and metadata.
    """

    type: ResourceType
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)


class Resource(Lifecycle, ABC):
    """Base class for all resources.

    This class defines the standard interface that all resources must implement,
    providing consistent lifecycle management and configuration.
    """

    def __init__(
        self,
        name: str,
        config: ResourceConfig,
    ) -> None:
        """Initialize the resource.

        Args:
            name: Resource name
            config: Resource configuration

        """
        super().__init__()
        self.name = name
        self.config = config
        self._state = ResourceState.UNINITIALIZED
        self._error: Optional[ResourceError] = None
        self._metadata: Dict[str, Any] = {}
        self._dependencies: Dict[str, Resource] = {}
        self._dependents: Set[str] = set()
        self._logger = get_logger(
            __name__,
            {
                "resource_name": name,
                "resource_type": config.type.value,
            },
        )

    @property
    def state(self) -> ResourceState:
        """Get the current state of the resource."""
        return self._state

    @property
    def error(self) -> Optional[ResourceError]:
        """Get the current error if any."""
        return self._error

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the resource metadata."""
        return self._metadata

    @property
    def dependencies(self) -> Dict[str, Resource]:
        """Get the resource dependencies."""
        return self._dependencies

    def set_error(
        self, message: str, error_type: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set an error on the resource.

        Args:
            message: The error message.
            error_type: The type of error.
            details: Optional error details.

        """
        self._error = ResourceError(
            message=message,
            resource_type=self.config.type,
            resource_name=self.name,
            details=details,
        )
        self._state = ResourceState.ERROR
        self._logger.error(message)

    def clear_error(self) -> None:
        """Clear any error on the resource."""
        self._error = None

    def add_dependency(self, name: str, resource: "Resource") -> None:
        """Add a dependency.

        Args:
            name: Dependency name
            resource: Resource to depend on

        Raises:
            ValueError: If dependency already exists
            ResourceOperationError: If dependency would create a cycle

        """
        if name in self._dependencies:
            raise ValueError(f"Dependency {name} already exists")

        # Check for dependency cycles
        if self._would_create_cycle(resource):
            raise ResourceOperationError(
                f"Adding dependency {name} would create a cycle"
            )

        self._dependencies[name] = resource
        resource._dependents.add(self.name)
        self._logger.info(f"Added dependency {name} to resource {self.name}")

    def remove_dependency(self, name: str) -> None:
        """Remove a dependency.

        Args:
            name: Dependency name

        Raises:
            ValueError: If dependency doesn't exist

        """
        if name not in self._dependencies:
            raise ValueError(f"Dependency {name} does not exist")

        resource = self._dependencies[name]
        del self._dependencies[name]
        resource._dependents.remove(self.name)
        self._logger.info(f"Removed dependency {name} from resource {self.name}")

    def get_dependency(self, name: str) -> Optional["Resource"]:
        """Get a dependency.

        Args:
            name: Dependency name

        Returns:
            Resource if found, None otherwise

        """
        return self._dependencies.get(name)

    def list_dependencies(self) -> List["Resource"]:
        """List all dependencies.

        Returns:
            List of dependencies

        """
        return list(self._dependencies.values())

    def list_dependents(self) -> List[str]:
        """List all dependents.

        Returns:
            List of dependent resource names

        """
        return list(self._dependents)

    def _would_create_cycle(self, resource: "Resource") -> bool:
        """Check if adding a dependency would create a cycle.

        Args:
            resource: Resource to check

        Returns:
            True if cycle would be created, False otherwise

        """
        visited = {self.name}
        stack = [resource]

        while stack:
            current = stack.pop()
            if current.name in visited:
                return True
            visited.add(current.name)
            stack.extend(current.list_dependencies())

        return False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the resource.

        This method should be implemented by subclasses to perform resource-specific
        initialization.

        Raises:
            ResourceError: If initialization fails

        """
        self._logger.info("Initializing resource")

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resource.

        This method should be implemented by subclasses to perform resource-specific
        cleanup.

        Raises:
            ResourceError: If cleanup fails

        """
        self._logger.info("Cleaning up resource")

    @abstractmethod
    async def validate(self) -> None:
        """Validate resource configuration and state.

        This method should be implemented by subclasses to validate that the
        resource is properly configured and in a valid state.

        Raises:
            ResourceError: If validation fails

        """
        if not self.config:
            raise ResourceError(
                "Resource configuration required",
                self.config.type,
                self.name,
            )

    async def get_status(self) -> Dict[str, Any]:
        """Get current resource status.

        Returns:
            Dictionary containing resource status information

        """
        return {
            "name": self.name,
            "type": self.config.type.value,
            "state": self.state.value if self.state else None,
            "metadata": self.config.metadata,
        }


class ResourceProvider(ABC):
    """Interface for resource providers.

    Resource providers are responsible for creating and managing resources of
    specific types, handling their lifecycle and configuration.
    """

    @abstractmethod
    async def create_resource(
        self,
        name: str,
        config: ResourceConfig,
    ) -> Resource:
        """Create a new resource instance.

        Args:
            name: Resource name
            config: Resource configuration

        Returns:
            Created resource instance

        Raises:
            ResourceError: If resource creation fails

        """
        pass

    @abstractmethod
    async def delete_resource(
        self,
        resource: Resource,
    ) -> None:
        """Delete a resource instance.

        Args:
            resource: Resource to delete

        Raises:
            ResourceError: If resource deletion fails

        """
        pass
