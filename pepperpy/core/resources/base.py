"""Base interfaces and types for resource management.

This module provides the core interfaces and types for managing resources in a
unified way, with support for lifecycle management and configuration.
"""

import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Type, TypeVar

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.monitoring.logging import get_logger

from .types import ResourceConfig, ResourceError, ResourceOperationError, ResourceState

if TYPE_CHECKING:
    from .base import Resource

T = TypeVar("T", bound="Resource")


class ResourceType(Enum):
    """Types of resources supported by the system."""

    STORAGE = "storage"  # File systems, databases, caches
    COMPUTE = "compute"  # Processing units, workers
    NETWORK = "network"  # Network connections, APIs
    MEMORY = "memory"  # Memory caches, buffers
    MODEL = "model"  # AI models, embeddings
    SERVICE = "service"  # External services


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

        Raises:
            ValueError: If name or config is invalid

        """
        if not name:
            raise ValueError("Resource name cannot be empty")
        if not config:
            raise ValueError("Resource configuration required")

        super().__init__()
        self._name = name
        self._config = config
        self._state = ResourceState.UNINITIALIZED
        self._error: Optional[ResourceError] = None
        self._metadata: Dict[str, Any] = {}
        self._dependencies: Dict[str, "Resource"] = {}
        self._dependents: Set[str] = set()
        self._logger = get_logger(f"{__name__}.{name}")

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
    def dependencies(self) -> Dict[str, "Resource"]:
        """Get the resource dependencies."""
        return self._dependencies

    @property
    def name(self) -> str:
        """Get the resource name."""
        return self._name

    def set_error(
        self, message: str, error_type: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set resource error.

        Args:
            message: Error message
            error_type: Type of error
            details: Optional error details

        """
        self._error = ResourceError(
            message=message,
            error_type=error_type,
            timestamp=float(time.time()),
            details=details,
        )
        self._state = ResourceState.ERROR
        self._logger.error(f"Resource error - {error_type}: {message}")

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
        resource._dependents.add(self._name)
        self._logger.info(f"Added dependency {name} to resource {self._name}")

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
        resource._dependents.remove(self._name)
        self._logger.info(f"Removed dependency {name} from resource {self._name}")

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
        visited = {self._name}
        stack = [resource]

        while stack:
            current = stack.pop()
            if current._name in visited:
                return True
            visited.add(current._name)
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
        """Validate the resource configuration.

        Raises:
            ResourceError: If validation fails.
            ValueError: If configuration is invalid.

        """
        if not self._config:
            raise ResourceError(
                message="Resource configuration required",
                error_type=str(ResourceType.STORAGE),
                timestamp=time.time(),
            )

    async def get_status(self) -> Dict[str, Any]:
        """Get current resource status.

        Returns:
            Dictionary containing resource status information

        """
        return {
            "name": self._name,
            "type": self._config.type.value,
            "state": self.state.value if self.state else None,
            "metadata": self._config.metadata,
        }

    @classmethod
    def get_resource_type(cls) -> Type["Resource"]:
        """Get the resource type.

        Returns:
            Resource type

        """
        return cls

    def __repr__(self) -> str:
        """Get string representation.

        Returns:
            String representation

        """
        return f"{self.__class__.__name__}(name={self._name})"


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
