"""Resource manager module for managing resource lifecycles."""

import asyncio
from typing import Dict, List, Optional, Set, Type, cast

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.monitoring import logger
from pepperpy.core.monitoring.metrics import Counter, Gauge, Histogram

from .base import Resource
from .types import ResourceConfig, ResourceError, ResourceOperationError, ResourceState


class ResourceManager(Lifecycle):
    """Manager for resource lifecycles.

    This class manages the lifecycle of resources, including initialization,
    cleanup, and dependency management.
    """

    def __init__(self) -> None:
        """Initialize resource manager."""
        super().__init__()
        self._resources: Dict[str, Resource] = {}
        self._resource_types: Dict[str, Type[Resource]] = {}
        self._state = ResourceState.UNINITIALIZED
        self._error: Optional[ResourceError] = None
        self._logger = logger

        # Metrics
        self._resource_count = Gauge(
            "resource_count",
            "Number of resources managed",
            tags={"component": "resource_manager"},
        )
        self._resource_errors = Counter(
            "resource_errors",
            "Number of resource errors",
            tags={"component": "resource_manager"},
        )
        self._resource_init_time = Histogram(
            "resource_init_time",
            "Time taken to initialize resources",
            tags={"component": "resource_manager"},
        )

    @property
    def resources(self) -> Dict[str, Resource]:
        """Get all managed resources."""
        return self._resources

    def register_resource_type(
        self,
        name: str,
        resource_class: Type[Resource],
    ) -> None:
        """Register a resource type.

        Args:
            name: Resource type name
            resource_class: Resource class

        Raises:
            ValueError: If resource type already registered

        """
        if name in self._resource_types:
            raise ValueError(f"Resource type {name} already registered")
        self._resource_types[name] = resource_class
        self._logger.info(f"Registered resource type {name}")

    def create_resource(
        self,
        name: str,
        config: ResourceConfig,
        resource_class: Optional[Type[Resource]] = None,
    ) -> Resource:
        """Create a resource.

        Args:
            name: Resource name
            config: Resource configuration
            resource_class: Optional resource class (if not using registered type)

        Returns:
            Created resource

        Raises:
            ValueError: If resource already exists
            ResourceOperationError: If resource type not found

        """
        if name in self._resources:
            raise ValueError(f"Resource {name} already exists")

        if resource_class is None:
            resource_type = config.type.value
            if resource_type not in self._resource_types:
                raise ResourceOperationError(f"Resource type {resource_type} not found")
            resource_class = self._resource_types[resource_type]

        resource = resource_class(name, cast(ResourceConfig, config))
        self._resources[name] = resource
        self._resource_count.increment()
        self._logger.info(f"Created resource {name}")
        return resource

    def get_resource(self, name: str) -> Optional[Resource]:
        """Get a resource by name.

        Args:
            name: Resource name

        Returns:
            Resource if found, None otherwise

        """
        return self._resources.get(name)

    def remove_resource(self, name: str) -> None:
        """Remove a resource.

        Args:
            name: Resource name

        Raises:
            ValueError: If resource not found
            ResourceOperationError: If resource has dependents

        """
        if name not in self._resources:
            raise ValueError(f"Resource {name} not found")

        resource = self._resources[name]
        if resource.list_dependents():
            raise ResourceOperationError(
                f"Cannot remove resource {name} with dependents"
            )

        del self._resources[name]
        self._resource_count.decrement()
        self._logger.info(f"Removed resource {name}")

    async def initialize(self) -> None:
        """Initialize all resources.

        This method initializes all resources in dependency order.

        Raises:
            ResourceError: If initialization fails

        """
        self._logger.info("Initializing resources")
        try:
            ordered_resources = self._get_initialization_order()
            for resource in ordered_resources:
                start_time = asyncio.get_event_loop().time()
                try:
                    await resource.initialize()
                except Exception as e:
                    self._resource_errors.increment()
                    raise ResourceError(
                        f"Failed to initialize resource {resource.name}: {str(e)}",
                        error_type="initialization_error",
                        timestamp=start_time,
                        details={"resource_name": resource.name},
                    ) from e
                finally:
                    end_time = asyncio.get_event_loop().time()
                    self._resource_init_time.observe(end_time - start_time)
            self._state = ResourceState.READY
            self._logger.info("Resources initialized")
        except Exception as e:
            self._state = ResourceState.ERROR
            self._error = ResourceError(
                str(e),
                error_type="initialization_error",
                timestamp=asyncio.get_event_loop().time(),
            )
            raise

    async def cleanup(self) -> None:
        """Clean up all resources.

        This method cleans up all resources in reverse dependency order.

        Raises:
            ResourceError: If cleanup fails

        """
        self._logger.info("Cleaning up resources")
        try:
            ordered_resources = reversed(self._get_initialization_order())
            for resource in ordered_resources:
                try:
                    await resource.cleanup()
                except Exception as e:
                    self._resource_errors.increment()
                    raise ResourceError(
                        f"Failed to clean up resource {resource.name}: {str(e)}",
                        error_type="cleanup_error",
                        timestamp=asyncio.get_event_loop().time(),
                        details={"resource_name": resource.name},
                    ) from e
            self._state = ResourceState.CLEANED
            self._logger.info("Resources cleaned up")
        except Exception as e:
            self._state = ResourceState.ERROR
            self._error = ResourceError(
                str(e),
                error_type="cleanup_error",
                timestamp=asyncio.get_event_loop().time(),
            )
            raise

    def _get_initialization_order(self) -> List[Resource]:
        """Get resources in dependency order.

        Returns:
            List of resources in initialization order

        Raises:
            ResourceOperationError: If dependency cycle detected

        """
        visited: Set[str] = set()
        temp_mark: Set[str] = set()
        order: List[Resource] = []

        def visit(resource: Resource) -> None:
            """Visit a resource in topological sort.

            Args:
                resource: Resource to visit

            Raises:
                ResourceOperationError: If dependency cycle detected

            """
            if resource.name in temp_mark:
                raise ResourceOperationError("Dependency cycle detected")
            if resource.name not in visited:
                temp_mark.add(resource.name)
                for dep in resource.list_dependencies():
                    visit(dep)
                temp_mark.remove(resource.name)
                visited.add(resource.name)
                order.append(resource)

        for resource in self._resources.values():
            if resource.name not in visited:
                visit(resource)

        return order


# Global resource manager instance
resource_manager = ResourceManager()
