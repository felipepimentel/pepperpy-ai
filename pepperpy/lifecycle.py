"""Lifecycle management for the PepperPy framework.

This module provides utilities for managing the lifecycle of components and resources
in the PepperPy framework. It includes functionality for initialization, configuration,
and disposal of resources.
"""

from typing import Any, Dict, Optional, Set, Type, TypeVar, cast

from pepperpy.core.base import Disposable, Initializable, Resource
from pepperpy.core.errors import DisposalError, InitializationError
from pepperpy.core.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

T = TypeVar("T")
ResourceType = TypeVar("ResourceType", bound=Resource)


class LifecycleManager:
    """Manages the lifecycle of components and resources.

    The lifecycle manager is responsible for tracking resources and ensuring
    they are properly initialized and disposed of.
    """

    def __init__(self):
        """Initialize the lifecycle manager."""
        self._resources: Set[Resource] = set()
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the lifecycle manager has been initialized.

        Returns:
            True if the lifecycle manager has been initialized, False otherwise
        """
        return self._initialized

    def register(self, resource: Resource) -> None:
        """Register a resource with the lifecycle manager.

        Args:
            resource: The resource to register
        """
        self._resources.add(resource)

    def unregister(self, resource: Resource) -> None:
        """Unregister a resource from the lifecycle manager.

        Args:
            resource: The resource to unregister
        """
        if resource in self._resources:
            self._resources.remove(resource)

    async def initialize_all(self) -> None:
        """Initialize all registered resources.

        This method initializes all registered resources that implement the
        Initializable interface. Resources are initialized in the order they
        were registered.

        Raises:
            InitializationError: If initialization of any resource fails
        """
        if self._initialized:
            logger.warning("Lifecycle manager is already initialized")
            return

        logger.info(f"Initializing {len(self._resources)} resources")

        errors = []

        for resource in self._resources:
            if isinstance(resource, Initializable):
                try:
                    logger.debug(f"Initializing resource: {resource}")
                    await resource.initialize()
                except Exception as e:
                    error_msg = f"Failed to initialize resource {resource}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        if errors:
            raise InitializationError(
                f"Failed to initialize {len(errors)} resources: {', '.join(errors)}"
            )

        self._initialized = True
        logger.info("All resources initialized successfully")

    async def dispose_all(self) -> None:
        """Dispose of all registered resources.

        This method disposes of all registered resources that implement the
        Disposable interface. Resources are disposed of in reverse order of
        registration to ensure proper dependency handling.

        Raises:
            DisposalError: If disposal of any resource fails
        """
        if not self._initialized:
            logger.warning("Lifecycle manager is not initialized")
            return

        logger.info(f"Disposing of {len(self._resources)} resources")

        errors = []
        resources = list(self._resources)

        # Dispose in reverse order of registration
        for resource in reversed(resources):
            if isinstance(resource, Disposable):
                try:
                    logger.debug(f"Disposing of resource: {resource}")
                    await resource.dispose()
                except Exception as e:
                    error_msg = f"Failed to dispose of resource {resource}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        if errors:
            raise DisposalError(
                f"Failed to dispose of {len(errors)} resources: {', '.join(errors)}"
            )

        self._resources.clear()
        self._initialized = False
        logger.info("All resources disposed successfully")


class ResourceManager:
    """Manages resources of different types."""

    def __init__(self):
        """Initialize the resource manager."""
        self._resources: Dict[Type[Any], Resource] = {}

    def register(self, resource: ResourceType) -> ResourceType:
        """Register a resource with the resource manager.

        Args:
            resource: The resource to register

        Returns:
            The registered resource
        """
        self._resources[type(resource)] = resource
        return resource

    def get(self, resource_type: Type[ResourceType]) -> Optional[ResourceType]:
        """Get a resource of the specified type.

        Args:
            resource_type: The type of resource to get

        Returns:
            The resource, or None if not found
        """
        return cast(Optional[ResourceType], self._resources.get(resource_type))

    def require(self, resource_type: Type[ResourceType]) -> ResourceType:
        """Get a resource of the specified type, raising an exception if not found.

        Args:
            resource_type: The type of resource to get

        Returns:
            The resource

        Raises:
            KeyError: If the resource is not found
        """
        resource = self.get(resource_type)
        if resource is None:
            raise KeyError(f"Resource of type {resource_type.__name__} not found")
        return resource

    async def initialize_all(self) -> None:
        """Initialize all registered resources.

        Raises:
            InitializationError: If initialization of any resource fails
        """
        lifecycle_manager = LifecycleManager()
        for resource in self._resources.values():
            lifecycle_manager.register(resource)
        await lifecycle_manager.initialize_all()

    async def dispose_all(self) -> None:
        """Dispose of all registered resources.

        Raises:
            DisposalError: If disposal of any resource fails
        """
        lifecycle_manager = LifecycleManager()
        for resource in self._resources.values():
            lifecycle_manager.register(resource)
        await lifecycle_manager.dispose_all()


# Global lifecycle manager instance
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get the global lifecycle manager instance.

    Returns:
        The global lifecycle manager instance
    """
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager()
    return _lifecycle_manager


def set_lifecycle_manager(manager: LifecycleManager) -> None:
    """Set the global lifecycle manager instance.

    Args:
        manager: The lifecycle manager instance to set
    """
    global _lifecycle_manager
    _lifecycle_manager = manager


async def initialize_framework() -> None:
    """Initialize the PepperPy framework.

    This function initializes all registered resources in the global
    lifecycle manager.

    Raises:
        InitializationError: If initialization fails
    """
    logger.info("Initializing PepperPy framework")
    await get_lifecycle_manager().initialize_all()
    logger.info("PepperPy framework initialized successfully")


async def shutdown_framework() -> None:
    """Shut down the PepperPy framework.

    This function disposes of all registered resources in the global
    lifecycle manager.

    Raises:
        DisposalError: If disposal fails
    """
    logger.info("Shutting down PepperPy framework")
    await get_lifecycle_manager().dispose_all()
    logger.info("PepperPy framework shut down successfully")


__all__ = [
    "LifecycleManager",
    "ResourceManager",
    "get_lifecycle_manager",
    "set_lifecycle_manager",
    "initialize_framework",
    "shutdown_framework",
]
