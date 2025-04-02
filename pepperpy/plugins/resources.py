"""Resource management for PepperPy plugins.

This module provides resource management functionality for PepperPy plugins,
including resource pooling, lazy initialization, and cleanup scheduling.
"""

import asyncio
import functools
import inspect
import time
import weakref
from collections import defaultdict
from datetime import datetime
from enum import Enum, IntEnum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from pepperpy.core.errors import ResourceError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type variables
T = TypeVar("T")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


class ResourceState(Enum):
    """State of a pooled resource."""

    # Resource is available for use
    AVAILABLE = "available"

    # Resource is in use by a plugin
    IN_USE = "in_use"

    # Resource is being initialized
    INITIALIZING = "initializing"

    # Resource is being cleaned up
    CLEANING_UP = "cleaning_up"

    # Resource has encountered an error
    ERROR = "error"

    # Resource has been closed/removed from pool
    CLOSED = "closed"


class InitializationPriority(IntEnum):
    """Priority levels for lazy initialization."""

    # Critical resources that should be initialized immediately when needed
    CRITICAL = 100

    # High priority resources that should be initialized soon after startup
    HIGH = 75

    # Normal priority resources
    NORMAL = 50

    # Low priority resources that can be initialized later
    LOW = 25

    # Background resources that should only be initialized when idle
    BACKGROUND = 0


class ResourceMetrics:
    """Metrics for resource usage and performance."""

    def __init__(self, resource_id: str, resource_type: str) -> None:
        """Initialize resource metrics.

        Args:
            resource_id: Unique identifier for the resource
            resource_type: Type of the resource
        """
        self.resource_id = resource_id
        self.resource_type = resource_type

        # Timestamps
        self.created_at = datetime.now()
        self.last_accessed = None
        self.last_released = None

        # Usage counts
        self.total_accesses = 0
        self.total_errors = 0
        self.current_acquisition_time = None

        # Time tracking
        self.total_time_in_use = 0.0
        self.max_time_in_use = 0.0
        self.initialization_time_ms = None

        # Error tracking
        self.last_error = None
        self.last_error_time = None

    def mark_access(self) -> None:
        """Mark the resource as accessed."""
        now = datetime.now()
        self.last_accessed = now
        self.current_acquisition_time = time.time()
        self.total_accesses += 1

    def mark_release(self) -> None:
        """Mark the resource as released."""
        now = datetime.now()
        self.last_released = now

        # Calculate time in use
        if self.current_acquisition_time is not None:
            time_in_use = time.time() - self.current_acquisition_time
            self.total_time_in_use += time_in_use
            self.max_time_in_use = max(self.max_time_in_use, time_in_use)
            self.current_acquisition_time = None

    def record_error(self, error: Exception) -> None:
        """Record an error.

        Args:
            error: The error that occurred
        """
        self.total_errors += 1
        self.last_error = error
        self.last_error_time = datetime.now()

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary.

        Returns:
            Dictionary of metrics
        """
        metrics = {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "last_released": self.last_released,
            "total_accesses": self.total_accesses,
            "total_errors": self.total_errors,
            "total_time_in_use": self.total_time_in_use,
            "max_time_in_use": self.max_time_in_use,
            "error_rate": (
                self.total_errors / self.total_accesses
                if self.total_accesses > 0
                else 0
            ),
            "initialization_time_ms": self.initialization_time_ms,
        }

        # Add currently accessed status
        if self.current_acquisition_time is not None:
            metrics["currently_in_use"] = True
            metrics["current_time_in_use"] = time.time() - self.current_acquisition_time
        else:
            metrics["currently_in_use"] = False
            metrics["current_time_in_use"] = 0

        return metrics


class ManagedResource(Generic[T]):
    """A managed resource that can be pooled, initialized, and cleaned up."""

    def __init__(
        self,
        resource_id: str,
        resource: T,
        resource_type: str,
        cleanup_func: Optional[Callable[[T], Any]] = None,
        priority: InitializationPriority = InitializationPriority.NORMAL,
    ) -> None:
        """Initialize a managed resource.

        Args:
            resource_id: Unique identifier for the resource
            resource: The resource object
            resource_type: Type of resource
            cleanup_func: Function to call for cleanup
            priority: Initialization priority
        """
        self.resource_id = resource_id
        self.resource = resource
        self.resource_type = resource_type
        self.cleanup_func = cleanup_func
        self.priority = priority
        self.state = ResourceState.AVAILABLE
        self.current_owner: Optional[str] = None
        self.metrics = ResourceMetrics(resource_id, resource_type)
        self.lock = asyncio.Lock()
        self.error: Optional[Exception] = None
        self.last_state_change = datetime.now()
        self.scheduled_cleanup_time: Optional[datetime] = None

    async def acquire(self, owner: str) -> T:
        """Acquire the resource.

        Args:
            owner: Identifier for the acquirer

        Returns:
            The resource

        Raises:
            ResourceError: If the resource is not available
        """
        async with self.lock:
            if self.state != ResourceState.AVAILABLE:
                raise ResourceError(
                    f"Resource {self.resource_id} is not available "
                    f"(current state: {self.state.value})"
                )

            # Change state and update metrics
            self.state = ResourceState.IN_USE
            self.current_owner = owner
            self.metrics.mark_access()
            self.last_state_change = datetime.now()
            
            # Cancel any scheduled cleanup
            self.scheduled_cleanup_time = None

            return self.resource

    async def release(self) -> None:
        """Release the resource.

        Raises:
            ResourceError: If the resource is not in use
        """
        async with self.lock:
            if self.state != ResourceState.IN_USE:
                raise ResourceError(
                    f"Resource {self.resource_id} is not in use "
                    f"(current state: {self.state.value})"
                )

            # Change state and update metrics
            self.state = ResourceState.AVAILABLE
            self.current_owner = None
            self.metrics.mark_release()
            self.last_state_change = datetime.now()

    async def cleanup(self) -> None:
        """Clean up the resource.

        Raises:
            ResourceError: If the resource is in use
        """
        async with self.lock:
            if self.state == ResourceState.IN_USE:
                raise ResourceError(
                    f"Cannot clean up resource {self.resource_id} while in use"
                )

            # Change state
            self.state = ResourceState.CLEANING_UP
            self.last_state_change = datetime.now()

            try:
                # Call cleanup function if available
                if self.cleanup_func:
                    if asyncio.iscoroutinefunction(self.cleanup_func):
                        await self.cleanup_func(self.resource)
                    else:
                        self.cleanup_func(self.resource)

                # Change state
                self.state = ResourceState.CLOSED
                self.last_state_change = datetime.now()
            except Exception as e:
                # Change state and record error
                self.state = ResourceState.ERROR
                self.error = e
                self.metrics.record_error(e)
                self.last_state_change = datetime.now()
                raise ResourceError(
                    f"Failed to clean up resource {self.resource_id}: {e}"
                ) from e


class ResourcePool:
    """Pool of managed resources."""

    def __init__(
        self,
        max_size: int = 10,
        idle_timeout_seconds: int = 300,
        cleanup_interval_seconds: int = 60,
    ) -> None:
        """Initialize resource pool.

        Args:
            max_size: Maximum number of resources in the pool
            idle_timeout_seconds: Seconds after which unused resources are cleaned up
            cleanup_interval_seconds: Interval in seconds for cleanup checks
        """
        self._resources: Dict[str, ManagedResource[Any]] = {}
        self._resource_by_type: Dict[str, Dict[str, ManagedResource[Any]]] = defaultdict(dict)
        self._lock = asyncio.Lock()
        self._max_size = max_size
        self._idle_timeout = idle_timeout_seconds
        self._cleanup_interval = cleanup_interval_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def start_cleanup_scheduler(self) -> None:
        """Start the cleanup scheduler."""
        if self._cleanup_task is not None:
            return

        self._shutdown = False
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.debug("Started resource pool cleanup scheduler")

    async def stop_cleanup_scheduler(self) -> None:
        """Stop the cleanup scheduler."""
        if self._cleanup_task is None:
            return

        self._shutdown = True
        self._cleanup_task.cancel()
        try:
            await self._cleanup_task
        except asyncio.CancelledError:
            pass
        self._cleanup_task = None
        logger.debug("Stopped resource pool cleanup scheduler")

    async def _cleanup_loop(self) -> None:
        """Loop to periodically clean up idle resources."""
        while not self._shutdown:
            try:
                await self._cleanup_idle_resources()
                await asyncio.sleep(self._cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource pool cleanup loop: {e}")
                await asyncio.sleep(self._cleanup_interval)

    async def _cleanup_idle_resources(self) -> None:
        """Clean up idle resources."""
        now = datetime.now()
        to_cleanup = []

        # Find resources to clean up
        async with self._lock:
            for resource_id, resource in list(self._resources.items()):
                if resource.state != ResourceState.AVAILABLE:
                    continue

                if resource.scheduled_cleanup_time is not None and now >= resource.scheduled_cleanup_time:
                    to_cleanup.append(resource)
                elif (
                    resource.metrics.last_released is not None
                    and (now - resource.metrics.last_released).total_seconds() >= self._idle_timeout
                ):
                    # Schedule cleanup
                    resource.scheduled_cleanup_time = now
                    logger.debug(f"Scheduling cleanup for idle resource: {resource_id}")

        # Clean up resources
        for resource in to_cleanup:
            try:
                logger.debug(f"Cleaning up idle resource: {resource.resource_id}")
                await resource.cleanup()
                async with self._lock:
                    self._remove_resource(resource.resource_id)
            except Exception as e:
                logger.error(f"Error cleaning up resource {resource.resource_id}: {e}")

    def _remove_resource(self, resource_id: str) -> None:
        """Remove a resource from the pool.

        Args:
            resource_id: ID of the resource to remove
        """
        if resource_id not in self._resources:
            return

        resource = self._resources[resource_id]
        del self._resources[resource_id]
        
        # Remove from resource_by_type
        resource_type = resource.resource_type
        if resource_type in self._resource_by_type and resource_id in self._resource_by_type[resource_type]:
            del self._resource_by_type[resource_type][resource_id]

        logger.debug(f"Removed resource from pool: {resource_id}")

    async def add_resource(
        self,
        resource_id: str,
        resource: Any,
        resource_type: str,
        cleanup_func: Optional[Callable[[Any], Any]] = None,
        priority: InitializationPriority = InitializationPriority.NORMAL,
    ) -> None:
        """Add a resource to the pool.

        Args:
            resource_id: Unique identifier for the resource
            resource: The resource object
            resource_type: Type of resource
            cleanup_func: Function to call for cleanup
            priority: Initialization priority

        Raises:
            ResourceError: If the pool is full or resource already exists
        """
        async with self._lock:
            if len(self._resources) >= self._max_size:
                raise ResourceError(f"Resource pool is full (max_size={self._max_size})")

            if resource_id in self._resources:
                raise ResourceError(f"Resource already exists in pool: {resource_id}")

            # Create managed resource
            managed = ManagedResource(
                resource_id, resource, resource_type, cleanup_func, priority
            )
            self._resources[resource_id] = managed
            self._resource_by_type[resource_type][resource_id] = managed

            logger.debug(f"Added resource to pool: {resource_id} (type={resource_type})")

    async def get_resource(
        self, resource_id: str, owner: str
    ) -> Any:
        """Get a resource from the pool.

        Args:
            resource_id: ID of the resource to get
            owner: Identifier for the acquirer

        Returns:
            The resource

        Raises:
            ResourceError: If the resource doesn't exist or can't be acquired
        """
        async with self._lock:
            if resource_id not in self._resources:
                raise ResourceError(f"Resource not found in pool: {resource_id}")

            resource = self._resources[resource_id]

        # Acquire the resource
        return await resource.acquire(owner)

    async def release_resource(self, resource_id: str) -> None:
        """Release a resource back to the pool.

        Args:
            resource_id: ID of the resource to release

        Raises:
            ResourceError: If the resource doesn't exist or can't be released
        """
        async with self._lock:
            if resource_id not in self._resources:
                raise ResourceError(f"Resource not found in pool: {resource_id}")

            resource = self._resources[resource_id]

        # Release the resource
        await resource.release()

    async def cleanup_resource(self, resource_id: str) -> None:
        """Clean up a resource and remove it from the pool.

        Args:
            resource_id: ID of the resource to clean up

        Raises:
            ResourceError: If the resource doesn't exist or can't be cleaned up
        """
        async with self._lock:
            if resource_id not in self._resources:
                raise ResourceError(f"Resource not found in pool: {resource_id}")

            resource = self._resources[resource_id]

        # Clean up the resource
        await resource.cleanup()

        # Remove from pool
        async with self._lock:
            self._remove_resource(resource_id)

    async def get_resource_by_type(
        self, resource_type: str, owner: str
    ) -> Tuple[str, Any]:
        """Get an available resource of a specific type.

        Args:
            resource_type: Type of resource to get
            owner: Identifier for the acquirer

        Returns:
            Tuple of (resource_id, resource)

        Raises:
            ResourceError: If no resources of the requested type are available
        """
        async with self._lock:
            if resource_type not in self._resource_by_type or not self._resource_by_type[resource_type]:
                raise ResourceError(f"No resources of type {resource_type} in pool")

            # Find available resource
            available_resources = [
                r for r in self._resource_by_type[resource_type].values()
                if r.state == ResourceState.AVAILABLE
            ]

            if not available_resources:
                raise ResourceError(f"No available resources of type {resource_type}")

            # Sort by priority and last accessed time
            available_resources.sort(
                key=lambda r: (
                    -r.priority,
                    r.metrics.last_accessed or datetime.min
                )
            )

            # Get highest priority resource that was least recently used
            resource = available_resources[0]
            resource_id = resource.resource_id

        # Acquire the resource
        return resource_id, await resource.acquire(owner)

    async def cleanup_all(self) -> None:
        """Clean up all resources in the pool."""
        # Stop cleanup scheduler if running
        await self.stop_cleanup_scheduler()

        # Get all resource IDs
        async with self._lock:
            resource_ids = list(self._resources.keys())

        # Clean up each resource
        for resource_id in resource_ids:
            try:
                await self.cleanup_resource(resource_id)
            except Exception as e:
                logger.error(f"Error cleaning up resource {resource_id}: {e}")

        # Clear dictionaries
        async with self._lock:
            self._resources.clear()
            self._resource_by_type.clear()

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all resources in the pool.

        Returns:
            Dictionary of resource metrics by resource ID
        """
        return {
            resource_id: resource.metrics.get_metrics()
            for resource_id, resource in self._resources.items()
        }


class ResourceMixin:
    """Mixin for classes that manage resources."""

    def __init__(self) -> None:
        """Initialize resource mixin."""
        self._resources: Dict[str, Any] = {}
        self._resource_cleanups: Dict[str, Callable[[], Any]] = {}
        self._resource_metrics: Dict[str, ResourceMetrics] = {}

    def _register_resource(
        self, name: str, resource: Any, cleanup: Optional[Callable[[], Any]] = None
    ) -> None:
        """Register a resource with optional cleanup.

        Args:
            name: Name of the resource
            resource: The resource object
            cleanup: Optional cleanup function
        """
        self._resources[name] = resource
        
        if cleanup:
            self._resource_cleanups[name] = cleanup
            
        self._resource_metrics[name] = ResourceMetrics(
            resource_id=name,
            resource_type=type(resource).__name__,
        )
        self._resource_metrics[name].mark_access()

    def _get_resource(self, name: str) -> Any:
        """Get a registered resource.

        Args:
            name: Name of the resource

        Returns:
            The resource

        Raises:
            ResourceError: If the resource is not registered
        """
        if name not in self._resources:
            raise ResourceError(f"Resource not registered: {name}")
            
        # Update metrics
        if name in self._resource_metrics:
            self._resource_metrics[name].mark_access()
            
        return self._resources[name]

    def _has_resource(self, name: str) -> bool:
        """Check if a resource is registered.

        Args:
            name: Name of the resource

        Returns:
            True if the resource is registered, False otherwise
        """
        return name in self._resources

    async def _cleanup_resources(self) -> None:
        """Clean up all registered resources."""
        errors = []

        # Clean up each resource
        for name, cleanup in list(self._resource_cleanups.items()):
            try:
                if asyncio.iscoroutinefunction(cleanup):
                    await cleanup()
                else:
                    cleanup()
                    
                # Update metrics
                if name in self._resource_metrics:
                    self._resource_metrics[name].mark_release()
                    
            except Exception as e:
                logger.error(f"Error cleaning up resource {name}: {e}")
                errors.append((name, e))
                
                # Update metrics
                if name in self._resource_metrics:
                    self._resource_metrics[name].record_error(e)

        # Clear dictionaries
        self._resources.clear()
        self._resource_cleanups.clear()

        # Raise error if any occurred
        if errors:
            names = ", ".join(name for name, _ in errors)
            raise ResourceError(f"Errors occurred during resource cleanup: {names}")


# Global resource pool
_resource_pool: Optional[ResourcePool] = None


def get_resource_pool() -> ResourcePool:
    """Get the global resource pool.

    Returns:
        Global resource pool instance
    """
    global _resource_pool
    if _resource_pool is None:
        _resource_pool = ResourcePool()
    return _resource_pool


async def cleanup_all_resources() -> None:
    """Clean up all resources in the global resource pool."""
    if _resource_pool is not None:
        await _resource_pool.cleanup_all()


# Decorator for lazy initialization
def lazy_initialize(
    func: Optional[F] = None,
    *,
    priority: InitializationPriority = InitializationPriority.NORMAL,
) -> Union[F, Callable[[F], F]]:
    """Decorator for lazy initialization of resources.

    Args:
        func: Function to decorate
        priority: Initialization priority

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        # Get resource name from function
        resource_name = func.__name__
        if resource_name.startswith("_"):
            resource_name = resource_name[1:]
        if resource_name.startswith("initialize_"):
            resource_name = resource_name[11:]

        @functools.wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Check if we have a resource attribute
            resource_attr = f"_{resource_name}"
            if hasattr(self, resource_attr) and getattr(self, resource_attr) is not None:
                return getattr(self, resource_attr)

            # Initialize the resource
            logger.debug(f"Lazy initializing resource: {resource_name}")
            start_time = time.time()
            result = await func(self, *args, **kwargs)
            end_time = time.time()

            # Store the resource
            setattr(self, resource_attr, result)

            # Register for cleanup if we have cleanup method
            cleanup_method = getattr(self, f"_cleanup_{resource_name}", None)
            if cleanup_method:
                if isinstance(self, ResourceMixin):
                    self._register_resource(resource_name, result, cleanup_method)

            # Record metrics
            initialization_time_ms = (end_time - start_time) * 1000
            logger.debug(
                f"Lazy initialized resource: {resource_name} "
                f"in {initialization_time_ms:.2f}ms"
            )

            return result

        return cast(F, wrapper)

    if func is None:
        return decorator
    return decorator(func)
