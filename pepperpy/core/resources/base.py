"""Base classes for resource management."""

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.monitoring import LoggerFactory

from .types import ResourceConfig, ResourceError, ResourceOperationError, ResourceState

if TYPE_CHECKING:
    from .base import Resource


class Resource(Lifecycle):
    """Base class for all resources."""

    def __init__(self, name: str, config: ResourceConfig):
        """Initialize a resource.

        Args:
            name: The name of the resource.
            config: The resource configuration.

        """
        super().__init__()
        self.name = name
        self.config = config
        self._state = ResourceState.UNINITIALIZED
        self._error: Optional[ResourceError] = None
        self._metadata: Dict[str, Any] = {}
        self._dependencies: Dict[str, Resource] = {}
        self._dependents: Set[str] = set()
        self._logger = LoggerFactory().get_logger(
            name="resource.base",
            context={
                "component": "Resource",
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
            error_type=error_type,
            timestamp=time.time(),
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

    async def initialize(self) -> None:
        """Initialize the resource and its dependencies.

        Raises:
            ResourceOperationError: If initialization fails

        """
        if self._state != ResourceState.UNINITIALIZED:
            return

        self._state = ResourceState.INITIALIZING
        self._logger.info("Initializing resource")

        try:
            # Initialize dependencies first
            for name, dependency in self._dependencies.items():
                try:
                    await dependency.initialize()
                except Exception as e:
                    raise ResourceOperationError(
                        f"Failed to initialize dependency {name}: {str(e)}"
                    ) from e

            await self._initialize()
            self._state = ResourceState.READY
            self._logger.info("Resource initialized successfully")
        except Exception as e:
            self._state = ResourceState.ERROR
            self._logger.error(
                "Failed to initialize resource",
                context={"error": str(e)},
            )
            raise

    async def cleanup(self) -> None:
        """Clean up the resource and its dependencies.

        Raises:
            ResourceOperationError: If cleanup fails

        """
        if self._state not in {ResourceState.READY, ResourceState.ERROR}:
            return

        # Check for dependent resources
        if self._dependents:
            raise ResourceOperationError(
                f"Cannot cleanup resource with dependents: {', '.join(self._dependents)}"
            )

        self._state = ResourceState.CLEANING
        self._logger.info("Cleaning up resource")

        try:
            await self._cleanup()
            self._state = ResourceState.CLEANED
            self._logger.info("Resource cleaned up successfully")

            # Clean up dependencies
            for name, dependency in self._dependencies.items():
                try:
                    await dependency.cleanup()
                except Exception as e:
                    self._logger.warning(
                        f"Failed to cleanup dependency {name}: {str(e)}",
                        context={"error": str(e)},
                    )
        except Exception as e:
            self._state = ResourceState.ERROR
            self._logger.error(
                "Failed to cleanup resource",
                context={"error": str(e)},
            )
            raise

    async def _initialize(self) -> None:
        """Internal initialization logic to be implemented by subclasses."""
        raise NotImplementedError("Resource must implement _initialize")

    async def _cleanup(self) -> None:
        """Internal cleanup logic to be implemented by subclasses."""
        raise NotImplementedError("Resource must implement _cleanup")
