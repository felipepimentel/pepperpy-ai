"""
Resource management for PepperPy plugins.

This module provides functionality for managing resources used by plugins.
Resources are objects that need to be acquired and released, such as
database connections, file handles, network sockets, or any other object
that requires proper cleanup.
"""

import asyncio
import enum
import threading
import time
import weakref
from contextlib import asynccontextmanager, contextmanager
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from pepperpy.core.errors import PluginError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ResourceType(enum.Enum):
    """Type of resource managed by the resource system."""

    # Database connections
    DATABASE = "database"

    # File handles
    FILE = "file"

    # Network connections
    NETWORK = "network"

    # Cache objects
    CACHE = "cache"

    # Thread pools
    THREAD_POOL = "thread_pool"

    # Process pools
    PROCESS_POOL = "process_pool"

    # Event loops
    EVENT_LOOP = "event_loop"

    # Locks, semaphores, etc.
    LOCK = "lock"

    # Memory resources like large arrays
    MEMORY = "memory"

    # GPU resources
    GPU = "gpu"

    # External API clients
    API_CLIENT = "api_client"

    # Custom resource type
    CUSTOM = "custom"


class ResourceError(PluginError):
    """Base class for resource-related errors."""

    pass


class ResourceNotFoundError(ResourceError):
    """Error raised when a resource is not found."""

    pass


class ResourceAlreadyExistsError(ResourceError):
    """Error raised when attempting to register a resource that already exists."""

    pass


class ResourceRegistry:
    """Registry for resources used by plugins."""

    def __init__(self):
        """Initialize the resource registry."""
        # Resources by owner and key
        self._resources: Dict[str, Dict[str, Any]] = {}

        # Resource metadata
        self._metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Cleanup functions by owner and key
        self._cleanup_funcs: Dict[
            str,
            Dict[str, Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]],
        ] = {}

        # Resources pending cleanup
        self._pending_cleanup: Set[Tuple[str, str]] = set()

        # Lock for thread safety
        self._lock = threading.RLock()

        # Finalizers to automatically clean up when objects are garbage collected
        self._finalizers: Dict[str, Dict[str, weakref.finalize]] = {}

    def register_resource(
        self,
        owner_id: str,
        resource_key: str,
        resource: Any,
        resource_type: Union[ResourceType, str] = ResourceType.CUSTOM,
        cleanup_func: Optional[
            Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]
        ] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_cleanup: bool = True,
    ) -> None:
        """Register a resource for a plugin.

        Args:
            owner_id: ID of the plugin that owns the resource
            resource_key: Unique key for the resource within the owner's scope
            resource: The resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call when cleaning up the resource
            metadata: Optional metadata about the resource
            auto_cleanup: Whether to automatically clean up the resource when it's garbage collected

        Raises:
            ResourceAlreadyExistsError: If a resource with the same key already exists for the owner
        """
        if isinstance(resource_type, str):
            # Convert string to enum if possible
            try:
                resource_type = ResourceType(resource_type)
            except ValueError:
                # Keep as string for custom resource types
                pass

        with self._lock:
            # Create owner entry if it doesn't exist
            if owner_id not in self._resources:
                self._resources[owner_id] = {}
                self._cleanup_funcs[owner_id] = {}
                self._metadata[owner_id] = {}
                self._finalizers[owner_id] = {}

            # Check if resource already exists
            if resource_key in self._resources[owner_id]:
                raise ResourceAlreadyExistsError(
                    f"Resource already exists: {owner_id}/{resource_key}"
                )

            # Register resource
            self._resources[owner_id][resource_key] = resource

            # Register cleanup function
            if cleanup_func:
                self._cleanup_funcs[owner_id][resource_key] = cleanup_func

            # Register metadata
            self._metadata[owner_id][resource_key] = {
                "type": resource_type.value
                if isinstance(resource_type, ResourceType)
                else resource_type,
                "registered_at": time.time(),
                **(metadata or {}),
            }

            # Set up finalizer for auto cleanup
            if auto_cleanup:

                def finalize_callback(
                    owner: str = owner_id,
                    key: str = resource_key,
                    res: Any = resource,
                    cleanup: Optional[Callable] = cleanup_func,
                ):
                    logger.debug(
                        f"Auto-cleaning resource due to garbage collection: {owner}/{key}"
                    )
                    try:
                        # Remove from registry
                        with self._lock:
                            if (
                                owner in self._resources
                                and key in self._resources[owner]
                            ):
                                del self._resources[owner][key]

                            if owner in self._metadata and key in self._metadata[owner]:
                                del self._metadata[owner][key]

                            if (
                                owner in self._cleanup_funcs
                                and key in self._cleanup_funcs[owner]
                            ):
                                del self._cleanup_funcs[owner][key]

                            if (
                                owner in self._finalizers
                                and key in self._finalizers[owner]
                            ):
                                del self._finalizers[owner][key]

                        # Call cleanup function
                        if cleanup:
                            if asyncio.iscoroutinefunction(cleanup):
                                # Create task for async cleanup
                                loop = asyncio.get_event_loop()
                                loop.create_task(cleanup(res))
                            else:
                                # Call synchronous cleanup
                                cleanup(res)
                    except Exception as e:
                        logger.error(
                            f"Error during auto-cleanup of resource {owner}/{key}: {e}"
                        )

                self._finalizers[owner_id][resource_key] = weakref.finalize(
                    resource, finalize_callback
                )

            logger.debug(
                f"Registered resource: {owner_id}/{resource_key} ({resource_type})"
            )

    def unregister_resource(self, owner_id: str, resource_key: str) -> Any:
        """Unregister a resource without cleaning it up.

        Args:
            owner_id: ID of the plugin that owns the resource
            resource_key: Unique key for the resource within the owner's scope

        Returns:
            The resource object

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        with self._lock:
            # Check if resource exists
            if (
                owner_id not in self._resources
                or resource_key not in self._resources[owner_id]
            ):
                raise ResourceNotFoundError(
                    f"Resource not found: {owner_id}/{resource_key}"
                )

            # Get resource
            resource = self._resources[owner_id][resource_key]

            # Remove resource
            del self._resources[owner_id][resource_key]

            # Remove metadata
            if owner_id in self._metadata and resource_key in self._metadata[owner_id]:
                del self._metadata[owner_id][resource_key]

            # Remove cleanup function
            if (
                owner_id in self._cleanup_funcs
                and resource_key in self._cleanup_funcs[owner_id]
            ):
                del self._cleanup_funcs[owner_id][resource_key]

            # Remove finalizer
            if (
                owner_id in self._finalizers
                and resource_key in self._finalizers[owner_id]
            ):
                # Disable finalizer
                self._finalizers[owner_id][resource_key].detach()
                del self._finalizers[owner_id][resource_key]

            logger.debug(f"Unregistered resource: {owner_id}/{resource_key}")
            return resource

    def get_resource(self, owner_id: str, resource_key: str) -> Any:
        """Get a resource.

        Args:
            owner_id: ID of the plugin that owns the resource
            resource_key: Unique key for the resource within the owner's scope

        Returns:
            The resource object

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        with self._lock:
            # Check if resource exists
            if (
                owner_id not in self._resources
                or resource_key not in self._resources[owner_id]
            ):
                raise ResourceNotFoundError(
                    f"Resource not found: {owner_id}/{resource_key}"
                )

            # Return resource
            return self._resources[owner_id][resource_key]

    def get_resource_metadata(self, owner_id: str, resource_key: str) -> Dict[str, Any]:
        """Get metadata for a resource.

        Args:
            owner_id: ID of the plugin that owns the resource
            resource_key: Unique key for the resource within the owner's scope

        Returns:
            Metadata for the resource

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        with self._lock:
            # Check if resource exists
            if (
                owner_id not in self._metadata
                or resource_key not in self._metadata[owner_id]
            ):
                raise ResourceNotFoundError(
                    f"Resource not found: {owner_id}/{resource_key}"
                )

            # Return metadata
            return self._metadata[owner_id][resource_key].copy()

    def has_resource(self, owner_id: str, resource_key: str) -> bool:
        """Check if a resource exists.

        Args:
            owner_id: ID of the plugin that owns the resource
            resource_key: Unique key for the resource within the owner's scope

        Returns:
            True if the resource exists, False otherwise
        """
        with self._lock:
            return (
                owner_id in self._resources
                and resource_key in self._resources[owner_id]
            )

    def get_resources_by_owner(self, owner_id: str) -> Dict[str, Any]:
        """Get all resources for an owner.

        Args:
            owner_id: ID of the plugin that owns the resources

        Returns:
            Dictionary of resource key to resource object
        """
        with self._lock:
            if owner_id not in self._resources:
                return {}

            return self._resources[owner_id].copy()

    def get_resources_by_type(
        self, resource_type: Union[ResourceType, str]
    ) -> Dict[str, Dict[str, Any]]:
        """Get all resources of a specific type.

        Args:
            resource_type: Type of resources to get

        Returns:
            Dictionary of owner ID to dictionary of resource key to resource object
        """
        type_value = (
            resource_type.value
            if isinstance(resource_type, ResourceType)
            else resource_type
        )

        result = {}
        with self._lock:
            for owner_id, metadata in self._metadata.items():
                for resource_key, meta in metadata.items():
                    if meta.get("type") == type_value:
                        if owner_id not in result:
                            result[owner_id] = {}

                        result[owner_id][resource_key] = self._resources[owner_id][
                            resource_key
                        ]

        return result

    async def cleanup_resource(self, owner_id: str, resource_key: str) -> None:
        """Clean up a resource.

        Args:
            owner_id: ID of the plugin that owns the resource
            resource_key: Unique key for the resource within the owner's scope

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        resource = None
        cleanup_func = None

        with self._lock:
            # Mark as pending cleanup
            self._pending_cleanup.add((owner_id, resource_key))

            try:
                # Check if resource exists
                if (
                    owner_id not in self._resources
                    or resource_key not in self._resources[owner_id]
                ):
                    raise ResourceNotFoundError(
                        f"Resource not found: {owner_id}/{resource_key}"
                    )

                # Get resource and cleanup function
                resource = self._resources[owner_id][resource_key]
                cleanup_func = self._cleanup_funcs.get(owner_id, {}).get(resource_key)

                # Remove finalizer
                if (
                    owner_id in self._finalizers
                    and resource_key in self._finalizers[owner_id]
                ):
                    # Disable finalizer
                    self._finalizers[owner_id][resource_key].detach()
                    del self._finalizers[owner_id][resource_key]
            finally:
                # Mark as no longer pending cleanup
                self._pending_cleanup.discard((owner_id, resource_key))

        # Call cleanup function outside of lock
        if cleanup_func:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    # Call async cleanup function
                    await cleanup_func(resource)
                else:
                    # Call synchronous cleanup function
                    cleanup_func(resource)
            except Exception as e:
                logger.error(
                    f"Error cleaning up resource {owner_id}/{resource_key}: {e}"
                )

        # Remove resource from registry
        with self._lock:
            if (
                owner_id in self._resources
                and resource_key in self._resources[owner_id]
            ):
                del self._resources[owner_id][resource_key]

            if owner_id in self._metadata and resource_key in self._metadata[owner_id]:
                del self._metadata[owner_id][resource_key]

            if (
                owner_id in self._cleanup_funcs
                and resource_key in self._cleanup_funcs[owner_id]
            ):
                del self._cleanup_funcs[owner_id][resource_key]

        logger.debug(f"Cleaned up resource: {owner_id}/{resource_key}")

    async def cleanup_owner_resources(self, owner_id: str) -> None:
        """Clean up all resources for an owner.

        Args:
            owner_id: ID of the plugin that owns the resources
        """
        # Get all resource keys for the owner
        with self._lock:
            if owner_id not in self._resources:
                return

            resource_keys = list(self._resources[owner_id].keys())

        # Clean up each resource
        for resource_key in resource_keys:
            try:
                await self.cleanup_resource(owner_id, resource_key)
            except ResourceNotFoundError:
                # Resource might have been cleaned up already
                pass
            except Exception as e:
                logger.error(
                    f"Error cleaning up resource {owner_id}/{resource_key}: {e}"
                )

        logger.debug(f"Cleaned up all resources for owner: {owner_id}")

    async def cleanup_all_resources(self) -> None:
        """Clean up all resources in the registry."""
        # Get all owner IDs
        with self._lock:
            owner_ids = list(self._resources.keys())

        # Clean up resources for each owner
        for owner_id in owner_ids:
            await self.cleanup_owner_resources(owner_id)

        logger.debug("Cleaned up all resources")

    @contextmanager
    def scoped_resource(
        self,
        owner_id: str,
        resource_key: str,
        resource: Any,
        resource_type: Union[ResourceType, str] = ResourceType.CUSTOM,
        cleanup_func: Optional[
            Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]
        ] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for a resource that automatically unregisters when the scope exits.

        Args:
            owner_id: ID of the plugin that owns the resource
            resource_key: Unique key for the resource within the owner's scope
            resource: The resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call when cleaning up the resource
            metadata: Optional metadata about the resource

        Yields:
            The resource object

        Raises:
            ResourceAlreadyExistsError: If a resource with the same key already exists for the owner
        """
        try:
            # Register resource
            self.register_resource(
                owner_id=owner_id,
                resource_key=resource_key,
                resource=resource,
                resource_type=resource_type,
                cleanup_func=cleanup_func,
                metadata=metadata,
                auto_cleanup=False,
            )

            # Yield resource
            yield resource
        finally:
            # Unregister resource
            try:
                # Only call cleanup function if provided
                if cleanup_func:
                    if asyncio.iscoroutinefunction(cleanup_func):
                        # Create task for async cleanup
                        loop = asyncio.get_event_loop()
                        loop.create_task(cleanup_func(resource))
                    else:
                        # Call synchronous cleanup
                        cleanup_func(resource)

                # Unregister without cleanup
                with self._lock:
                    if (
                        owner_id in self._resources
                        and resource_key in self._resources[owner_id]
                    ):
                        del self._resources[owner_id][resource_key]

                    if (
                        owner_id in self._metadata
                        and resource_key in self._metadata[owner_id]
                    ):
                        del self._metadata[owner_id][resource_key]

                    if (
                        owner_id in self._cleanup_funcs
                        and resource_key in self._cleanup_funcs[owner_id]
                    ):
                        del self._cleanup_funcs[owner_id][resource_key]

                    if (
                        owner_id in self._finalizers
                        and resource_key in self._finalizers[owner_id]
                    ):
                        # Disable finalizer
                        self._finalizers[owner_id][resource_key].detach()
                        del self._finalizers[owner_id][resource_key]
            except Exception as e:
                logger.error(
                    f"Error unregistering resource {owner_id}/{resource_key}: {e}"
                )

    @asynccontextmanager
    async def async_scoped_resource(
        self,
        owner_id: str,
        resource_key: str,
        resource: Any,
        resource_type: Union[ResourceType, str] = ResourceType.CUSTOM,
        cleanup_func: Optional[
            Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]
        ] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Async context manager for a resource that automatically unregisters when the scope exits.

        Args:
            owner_id: ID of the plugin that owns the resource
            resource_key: Unique key for the resource within the owner's scope
            resource: The resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call when cleaning up the resource
            metadata: Optional metadata about the resource

        Yields:
            The resource object

        Raises:
            ResourceAlreadyExistsError: If a resource with the same key already exists for the owner
        """
        try:
            # Register resource
            self.register_resource(
                owner_id=owner_id,
                resource_key=resource_key,
                resource=resource,
                resource_type=resource_type,
                cleanup_func=cleanup_func,
                metadata=metadata,
                auto_cleanup=False,
            )

            # Yield resource
            yield resource
        finally:
            # Clean up resource
            try:
                await self.cleanup_resource(owner_id, resource_key)
            except ResourceNotFoundError:
                # Resource might have been cleaned up already
                pass
            except Exception as e:
                logger.error(
                    f"Error cleaning up resource {owner_id}/{resource_key}: {e}"
                )


# Singleton instance
_resource_registry = ResourceRegistry()


# Convenience functions
def register_resource(
    owner_id: str,
    resource_key: str,
    resource: Any,
    resource_type: Union[ResourceType, str] = ResourceType.CUSTOM,
    cleanup_func: Optional[
        Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]
    ] = None,
    metadata: Optional[Dict[str, Any]] = None,
    auto_cleanup: bool = True,
) -> None:
    """Register a resource for a plugin.

    Args:
        owner_id: ID of the plugin that owns the resource
        resource_key: Unique key for the resource within the owner's scope
        resource: The resource object
        resource_type: Type of the resource
        cleanup_func: Optional function to call when cleaning up the resource
        metadata: Optional metadata about the resource
        auto_cleanup: Whether to automatically clean up the resource when it's garbage collected

    Raises:
        ResourceAlreadyExistsError: If a resource with the same key already exists for the owner
    """
    _resource_registry.register_resource(
        owner_id,
        resource_key,
        resource,
        resource_type,
        cleanup_func,
        metadata,
        auto_cleanup,
    )


def unregister_resource(owner_id: str, resource_key: str) -> Any:
    """Unregister a resource without cleaning it up.

    Args:
        owner_id: ID of the plugin that owns the resource
        resource_key: Unique key for the resource within the owner's scope

    Returns:
        The resource object

    Raises:
        ResourceNotFoundError: If the resource is not found
    """
    return _resource_registry.unregister_resource(owner_id, resource_key)


def get_resource(owner_id: str, resource_key: str) -> Any:
    """Get a resource.

    Args:
        owner_id: ID of the plugin that owns the resource
        resource_key: Unique key for the resource within the owner's scope

    Returns:
        The resource object

    Raises:
        ResourceNotFoundError: If the resource is not found
    """
    return _resource_registry.get_resource(owner_id, resource_key)


def get_resource_metadata(owner_id: str, resource_key: str) -> Dict[str, Any]:
    """Get metadata for a resource.

    Args:
        owner_id: ID of the plugin that owns the resource
        resource_key: Unique key for the resource within the owner's scope

    Returns:
        Metadata for the resource

    Raises:
        ResourceNotFoundError: If the resource is not found
    """
    return _resource_registry.get_resource_metadata(owner_id, resource_key)


def has_resource(owner_id: str, resource_key: str) -> bool:
    """Check if a resource exists.

    Args:
        owner_id: ID of the plugin that owns the resource
        resource_key: Unique key for the resource within the owner's scope

    Returns:
        True if the resource exists, False otherwise
    """
    return _resource_registry.has_resource(owner_id, resource_key)


def get_resources_by_owner(owner_id: str) -> Dict[str, Any]:
    """Get all resources for an owner.

    Args:
        owner_id: ID of the plugin that owns the resources

    Returns:
        Dictionary of resource key to resource object
    """
    return _resource_registry.get_resources_by_owner(owner_id)


def get_resources_by_type(
    resource_type: Union[ResourceType, str],
) -> Dict[str, Dict[str, Any]]:
    """Get all resources of a specific type.

    Args:
        resource_type: Type of resources to get

    Returns:
        Dictionary of owner ID to dictionary of resource key to resource object
    """
    return _resource_registry.get_resources_by_type(resource_type)


async def cleanup_resource(owner_id: str, resource_key: str) -> None:
    """Clean up a resource.

    Args:
        owner_id: ID of the plugin that owns the resource
        resource_key: Unique key for the resource within the owner's scope

    Raises:
        ResourceNotFoundError: If the resource is not found
    """
    await _resource_registry.cleanup_resource(owner_id, resource_key)


async def cleanup_owner_resources(owner_id: str) -> None:
    """Clean up all resources for an owner.

    Args:
        owner_id: ID of the plugin that owns the resources
    """
    await _resource_registry.cleanup_owner_resources(owner_id)


async def cleanup_all_resources() -> None:
    """Clean up all resources in the registry."""
    await _resource_registry.cleanup_all_resources()


def scoped_resource(
    owner_id: str,
    resource_key: str,
    resource: Any,
    resource_type: Union[ResourceType, str] = ResourceType.CUSTOM,
    cleanup_func: Optional[
        Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]
    ] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Context manager for a resource that automatically unregisters when the scope exits.

    Args:
        owner_id: ID of the plugin that owns the resource
        resource_key: Unique key for the resource within the owner's scope
        resource: The resource object
        resource_type: Type of the resource
        cleanup_func: Optional function to call when cleaning up the resource
        metadata: Optional metadata about the resource

    Returns:
        Context manager that yields the resource object

    Raises:
        ResourceAlreadyExistsError: If a resource with the same key already exists for the owner
    """
    return _resource_registry.scoped_resource(
        owner_id, resource_key, resource, resource_type, cleanup_func, metadata
    )


def async_scoped_resource(
    owner_id: str,
    resource_key: str,
    resource: Any,
    resource_type: Union[ResourceType, str] = ResourceType.CUSTOM,
    cleanup_func: Optional[
        Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]
    ] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Async context manager for a resource that automatically unregisters when the scope exits.

    Args:
        owner_id: ID of the plugin that owns the resource
        resource_key: Unique key for the resource within the owner's scope
        resource: The resource object
        resource_type: Type of the resource
        cleanup_func: Optional function to call when cleaning up the resource
        metadata: Optional metadata about the resource

    Returns:
        Async context manager that yields the resource object

    Raises:
        ResourceAlreadyExistsError: If a resource with the same key already exists for the owner
    """
    return _resource_registry.async_scoped_resource(
        owner_id, resource_key, resource, resource_type, cleanup_func, metadata
    )


class ResourceMixin:
    """Mixin class for plugins to manage resources."""

    def __init__(self, *args, **kwargs):
        """Initialize the resource mixin.

        This method should be called from the plugin's __init__ method.
        """
        self._resource_owner_id = getattr(self, "plugin_id", self.__class__.__name__)
        super().__init__(*args, **kwargs)

    def register_resource(
        self,
        resource_key: str,
        resource: Any,
        resource_type: Union[ResourceType, str] = ResourceType.CUSTOM,
        cleanup_func: Optional[
            Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]
        ] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_cleanup: bool = True,
    ) -> None:
        """Register a resource.

        Args:
            resource_key: Unique key for the resource within the plugin's scope
            resource: The resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call when cleaning up the resource
            metadata: Optional metadata about the resource
            auto_cleanup: Whether to automatically clean up the resource when it's garbage collected

        Raises:
            ResourceAlreadyExistsError: If a resource with the same key already exists for the plugin
        """
        register_resource(
            self._resource_owner_id,
            resource_key,
            resource,
            resource_type,
            cleanup_func,
            metadata,
            auto_cleanup,
        )

    def unregister_resource(self, resource_key: str) -> Any:
        """Unregister a resource without cleaning it up.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Returns:
            The resource object

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        return unregister_resource(self._resource_owner_id, resource_key)

    def get_resource(self, resource_key: str) -> Any:
        """Get a resource.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Returns:
            The resource object

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        return get_resource(self._resource_owner_id, resource_key)

    def get_resource_metadata(self, resource_key: str) -> Dict[str, Any]:
        """Get metadata for a resource.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Returns:
            Metadata for the resource

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        return get_resource_metadata(self._resource_owner_id, resource_key)

    def has_resource(self, resource_key: str) -> bool:
        """Check if a resource exists.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Returns:
            True if the resource exists, False otherwise
        """
        return has_resource(self._resource_owner_id, resource_key)

    def get_resources(self) -> Dict[str, Any]:
        """Get all resources for the plugin.

        Returns:
            Dictionary of resource key to resource object
        """
        return get_resources_by_owner(self._resource_owner_id)

    async def cleanup_resource(self, resource_key: str) -> None:
        """Clean up a resource.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        await cleanup_resource(self._resource_owner_id, resource_key)

    async def cleanup_all_resources(self) -> None:
        """Clean up all resources for the plugin."""
        await cleanup_owner_resources(self._resource_owner_id)

    def scoped_resource(
        self,
        resource_key: str,
        resource: Any,
        resource_type: Union[ResourceType, str] = ResourceType.CUSTOM,
        cleanup_func: Optional[
            Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]
        ] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for a resource that automatically unregisters when the scope exits.

        Args:
            resource_key: Unique key for the resource within the plugin's scope
            resource: The resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call when cleaning up the resource
            metadata: Optional metadata about the resource

        Returns:
            Context manager that yields the resource object

        Raises:
            ResourceAlreadyExistsError: If a resource with the same key already exists for the plugin
        """
        return scoped_resource(
            self._resource_owner_id,
            resource_key,
            resource,
            resource_type,
            cleanup_func,
            metadata,
        )

    def async_scoped_resource(
        self,
        resource_key: str,
        resource: Any,
        resource_type: Union[ResourceType, str] = ResourceType.CUSTOM,
        cleanup_func: Optional[
            Union[Callable[[Any], None], Callable[[Any], asyncio.Future]]
        ] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Async context manager for a resource that automatically unregisters when the scope exits.

        Args:
            resource_key: Unique key for the resource within the plugin's scope
            resource: The resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call when cleaning up the resource
            metadata: Optional metadata about the resource

        Returns:
            Async context manager that yields the resource object

        Raises:
            ResourceAlreadyExistsError: If a resource with the same key already exists for the plugin
        """
        return async_scoped_resource(
            self._resource_owner_id,
            resource_key,
            resource,
            resource_type,
            cleanup_func,
            metadata,
        )
