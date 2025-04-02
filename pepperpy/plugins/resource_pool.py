"""Resource pooling for PepperPy plugins.

This module provides enhanced resource pooling capabilities, including
shared resource pools, usage analytics, and dynamic scaling.
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Set,
    TypeVar,
    Union,
)

from pepperpy.core.errors import ResourceError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type variable for resource types
T = TypeVar("T")


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


class ResourceUsageMetrics:
    """Metrics for resource usage."""

    def __init__(self, resource_id: str, resource_type: str) -> None:
        """Initialize resource usage metrics.

        Args:
            resource_id: Unique identifier for the resource
            resource_type: Type of the resource
        """
        self.resource_id = resource_id
        self.resource_type = resource_type

        # Timestamps
        self.created_at = datetime.now()
        self.last_acquired = None
        self.last_released = None

        # Usage counts
        self.total_acquisitions = 0
        self.total_errors = 0
        self.current_acquisition_time = None

        # Time tracking
        self.total_time_in_use = 0.0
        self.max_time_in_use = 0.0

        # Error tracking
        self.last_error = None
        self.last_error_time = None

    def acquired(self) -> None:
        """Mark the resource as acquired."""
        now = datetime.now()
        self.last_acquired = now
        self.current_acquisition_time = time.time()
        self.total_acquisitions += 1

    def released(self) -> None:
        """Mark the resource as released."""
        now = datetime.now()
        self.last_released = now

        # Calculate time in use
        if self.current_acquisition_time is not None:
            time_in_use = time.time() - self.current_acquisition_time
            self.total_time_in_use += time_in_use
            self.max_time_in_use = max(self.max_time_in_use, time_in_use)
            self.current_acquisition_time = None

    def error_occurred(self, error: Exception) -> None:
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
            "last_acquired": self.last_acquired,
            "last_released": self.last_released,
            "total_acquisitions": self.total_acquisitions,
            "total_errors": self.total_errors,
            "total_time_in_use": self.total_time_in_use,
            "max_time_in_use": self.max_time_in_use,
            "average_time_in_use": (
                self.total_time_in_use / self.total_acquisitions
                if self.total_acquisitions > 0
                else 0
            ),
            "error_rate": (
                self.total_errors / self.total_acquisitions
                if self.total_acquisitions > 0
                else 0
            ),
            "last_error": str(self.last_error) if self.last_error else None,
            "last_error_time": self.last_error_time,
        }

        # Add currently acquired status
        if self.current_acquisition_time is not None:
            metrics["currently_in_use"] = True
            metrics["current_time_in_use"] = time.time() - self.current_acquisition_time
        else:
            metrics["currently_in_use"] = False
            metrics["current_time_in_use"] = 0

        return metrics


class PooledResource(Generic[T]):
    """A resource in a resource pool."""

    def __init__(
        self,
        resource_id: str,
        resource: T,
        resource_type: str,
        cleanup_func: Optional[Callable[[T], Any]] = None,
    ) -> None:
        """Initialize a pooled resource.

        Args:
            resource_id: Unique identifier for the resource
            resource: The actual resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call for cleanup
        """
        self.resource_id = resource_id
        self.resource = resource
        self.resource_type = resource_type
        self.cleanup_func = cleanup_func
        self.state = ResourceState.AVAILABLE
        self.current_owner: Optional[str] = None
        self.metrics = ResourceUsageMetrics(resource_id, resource_type)
        self.lock = asyncio.Lock()
        self.last_state_change = datetime.now()
        self.error: Optional[Exception] = None

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

            self.state = ResourceState.IN_USE
            self.current_owner = owner
            self.last_state_change = datetime.now()
            self.metrics.acquired()

            logger.debug(f"Resource {self.resource_id} acquired by {owner}")
            return self.resource

    async def release(self, owner: Optional[str] = None) -> None:
        """Release the resource.

        Args:
            owner: Optional identifier for the releaser

        Raises:
            ResourceError: If the resource is not in use or is owned by someone else
        """
        async with self.lock:
            if self.state != ResourceState.IN_USE:
                raise ResourceError(
                    f"Resource {self.resource_id} is not in use "
                    f"(current state: {self.state.value})"
                )

            if owner is not None and self.current_owner != owner:
                raise ResourceError(
                    f"Resource {self.resource_id} is owned by {self.current_owner}, "
                    f"not {owner}"
                )

            self.state = ResourceState.AVAILABLE
            self.current_owner = None
            self.last_state_change = datetime.now()
            self.metrics.released()

            logger.debug(
                f"Resource {self.resource_id} released"
                + (f" by {owner}" if owner else "")
            )

    async def mark_error(self, error: Exception) -> None:
        """Mark the resource as having an error.

        Args:
            error: The error that occurred
        """
        async with self.lock:
            self.state = ResourceState.ERROR
            self.error = error
            self.last_state_change = datetime.now()
            self.metrics.error_occurred(error)

            logger.error(f"Resource {self.resource_id} encountered an error: {error}")

    async def close(self) -> None:
        """Close and clean up the resource."""
        async with self.lock:
            if self.state == ResourceState.CLOSED:
                return

            if self.state == ResourceState.IN_USE:
                logger.warning(
                    f"Resource {self.resource_id} is being closed while in use "
                    f"by {self.current_owner}"
                )

            self.state = ResourceState.CLEANING_UP
            self.last_state_change = datetime.now()

            try:
                # Call cleanup function if provided
                if self.cleanup_func:
                    if asyncio.iscoroutinefunction(self.cleanup_func):
                        await self.cleanup_func(self.resource)
                    else:
                        self.cleanup_func(self.resource)

                # Try standard cleanup methods
                elif hasattr(self.resource, "close") and callable(self.resource.close):
                    close_func = self.resource.close
                    if asyncio.iscoroutinefunction(close_func):
                        await close_func()
                    else:
                        close_func()

                elif hasattr(self.resource, "cleanup") and callable(
                    self.resource.cleanup
                ):
                    cleanup_func = self.resource.cleanup
                    if asyncio.iscoroutinefunction(cleanup_func):
                        await cleanup_func()
                    else:
                        cleanup_func()

                elif hasattr(self.resource, "__aexit__") and callable(
                    self.resource.__aexit__
                ):
                    await self.resource.__aexit__(None, None, None)

                elif hasattr(self.resource, "__exit__") and callable(
                    self.resource.__exit__
                ):
                    self.resource.__exit__(None, None, None)

                logger.debug(f"Resource {self.resource_id} cleaned up successfully")

            except Exception as e:
                logger.error(f"Error cleaning up resource {self.resource_id}: {e}")
                self.error = e

            finally:
                self.state = ResourceState.CLOSED
                self.last_state_change = datetime.now()
                self.current_owner = None


class ResourcePoolMetrics:
    """Metrics for a resource pool."""

    def __init__(self, pool_id: str, resource_type: str) -> None:
        """Initialize resource pool metrics.

        Args:
            pool_id: Unique identifier for the pool
            resource_type: Type of resources in the pool
        """
        self.pool_id = pool_id
        self.resource_type = resource_type

        # Pool stats
        self.created_at = datetime.now()
        self.last_scaled_at = None
        self.total_acquisitions = 0
        self.total_releases = 0
        self.total_failures = 0
        self.total_creations = 0
        self.total_removals = 0

        # Size tracking
        self.min_size = 0
        self.max_size = 0
        self.scaling_events = 0

    def resource_created(self) -> None:
        """Record that a resource was created."""
        self.total_creations += 1
        self.last_scaled_at = datetime.now()
        self.scaling_events += 1

    def resource_removed(self) -> None:
        """Record that a resource was removed."""
        self.total_removals += 1
        self.last_scaled_at = datetime.now()
        self.scaling_events += 1

    def acquisition_attempt(self, success: bool) -> None:
        """Record an acquisition attempt.

        Args:
            success: Whether the acquisition succeeded
        """
        if success:
            self.total_acquisitions += 1
        else:
            self.total_failures += 1

    def resource_released(self) -> None:
        """Record that a resource was released."""
        self.total_releases += 1

    def update_size_stats(self, current_size: int) -> None:
        """Update size statistics.

        Args:
            current_size: Current size of the pool
        """
        if self.min_size == 0 or current_size < self.min_size:
            self.min_size = current_size

        if current_size > self.max_size:
            self.max_size = current_size

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary.

        Returns:
            Dictionary of metrics
        """
        return {
            "pool_id": self.pool_id,
            "resource_type": self.resource_type,
            "created_at": self.created_at,
            "last_scaled_at": self.last_scaled_at,
            "total_acquisitions": self.total_acquisitions,
            "total_releases": self.total_releases,
            "total_failures": self.total_failures,
            "total_creations": self.total_creations,
            "total_removals": self.total_removals,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "scaling_events": self.scaling_events,
            "failure_rate": (
                self.total_failures / (self.total_acquisitions + self.total_failures)
                if (self.total_acquisitions + self.total_failures) > 0
                else 0
            ),
        }


class ResourcePool(Generic[T]):
    """Pool of resources that can be shared between plugins."""

    def __init__(
        self,
        pool_id: str,
        resource_type: str,
        factory: Callable[[], Union[T, asyncio.Future[T]]],
        initial_size: int = 1,
        min_size: int = 1,
        max_size: int = 10,
        max_idle: int = 5,
        cleanup_func: Optional[Callable[[T], Any]] = None,
    ) -> None:
        """Initialize a resource pool.

        Args:
            pool_id: Unique identifier for the pool
            resource_type: Type of resources in the pool
            factory: Function to create new resources
            initial_size: Initial number of resources in the pool
            min_size: Minimum number of resources in the pool
            max_size: Maximum number of resources in the pool
            max_idle: Maximum number of idle resources to keep
            cleanup_func: Optional function to call for cleanup
        """
        self.pool_id = pool_id
        self.resource_type = resource_type
        self.factory = factory
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle = max_idle
        self.cleanup_func = cleanup_func

        self._resources: Dict[str, PooledResource[T]] = {}
        self._available_resources: Set[str] = set()
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)
        self._next_resource_id = 0
        self._closing = False
        self._metrics = ResourcePoolMetrics(pool_id, resource_type)

        # Automatic scaling settings
        self._auto_scaling_enabled = True
        self._scale_up_threshold = 0.8  # Scale up when 80% of resources are in use
        self._scale_down_threshold = 0.3  # Scale down when 30% of resources are in use

        # Initialize with the initial size
        self._initial_size = initial_size

    async def initialize(self) -> None:
        """Initialize the pool with resources."""
        async with self._lock:
            # Create initial resources
            for _ in range(self._initial_size):
                await self._create_resource()

            # Update metrics
            self._metrics.update_size_stats(len(self._resources))

    async def _create_resource(self) -> str:
        """Create a new resource and add it to the pool.

        Returns:
            Resource ID of the created resource

        Raises:
            ResourceError: If resource creation fails
        """
        resource_id = f"{self.pool_id}_{self._next_resource_id}"
        self._next_resource_id += 1

        try:
            # Create the resource
            if asyncio.iscoroutinefunction(self.factory):
                resource = await self.factory()
            else:
                resource_or_future = self.factory()
                if isinstance(resource_or_future, asyncio.Future):
                    resource = await resource_or_future
                else:
                    resource = resource_or_future

            # Add to pool
            pooled_resource = PooledResource(
                resource_id, resource, self.resource_type, self.cleanup_func
            )
            self._resources[resource_id] = pooled_resource
            self._available_resources.add(resource_id)

            # Update metrics
            self._metrics.resource_created()

            logger.debug(f"Created resource {resource_id} in pool {self.pool_id}")
            return resource_id

        except Exception as e:
            logger.error(f"Failed to create resource in pool {self.pool_id}: {e}")
            raise ResourceError(
                f"Failed to create resource in pool {self.pool_id}: {e}"
            ) from e

    async def acquire(
        self, owner: str = "unknown", timeout: Optional[float] = None
    ) -> T:
        """Acquire a resource from the pool.

        Args:
            owner: Identifier for the acquirer
            timeout: Optional timeout in seconds

        Returns:
            Resource from the pool

        Raises:
            ResourceError: If no resource is available and can't create more
            asyncio.TimeoutError: If timeout is reached
        """
        if self._closing:
            raise ResourceError(f"Resource pool {self.pool_id} is closing")

        # Try to get a resource with timeout
        try:
            return await asyncio.wait_for(self._acquire_impl(owner), timeout)
        except asyncio.TimeoutError:
            self._metrics.acquisition_attempt(False)
            logger.warning(
                f"Timeout waiting for resource from pool {self.pool_id} "
                f"for {owner} (timeout: {timeout}s)"
            )
            raise

    async def _acquire_impl(self, owner: str) -> T:
        """Implementation of acquire logic.

        Args:
            owner: Identifier for the acquirer

        Returns:
            Resource from the pool

        Raises:
            ResourceError: If no resource is available and can't create more
        """
        async with self._condition:
            # First, try to get an available resource
            while not self._available_resources and not self._closing:
                # If we can create more resources, do so
                if len(self._resources) < self.max_size:
                    try:
                        resource_id = await self._create_resource()
                        break
                    except Exception as e:
                        # If creation fails, wait for an available resource
                        logger.warning(
                            f"Failed to create additional resource in pool {self.pool_id}: {e}"
                        )
                        await self._condition.wait()
                else:
                    # Wait for a resource to become available
                    await self._condition.wait()

            if self._closing:
                self._metrics.acquisition_attempt(False)
                raise ResourceError(f"Resource pool {self.pool_id} is closing")

            # Get an available resource
            if self._available_resources:
                resource_id = next(iter(self._available_resources))
                self._available_resources.remove(resource_id)

                try:
                    pooled_resource = self._resources[resource_id]
                    resource = await pooled_resource.acquire(owner)
                    self._metrics.acquisition_attempt(True)

                    # Check if we should scale up
                    await self._check_scaling()

                    return resource

                except Exception as e:
                    # Put the resource back in the available set if acquisition fails
                    self._available_resources.add(resource_id)
                    self._metrics.acquisition_attempt(False)
                    logger.error(f"Error acquiring resource {resource_id}: {e}")
                    raise ResourceError(
                        f"Error acquiring resource from pool {self.pool_id}: {e}"
                    ) from e

            # This should not happen due to the loop above, but just in case
            self._metrics.acquisition_attempt(False)
            raise ResourceError(f"No resource available in pool {self.pool_id}")

    async def release(self, resource: T, owner: Optional[str] = None) -> None:
        """Release a resource back to the pool.

        Args:
            resource: The resource to release
            owner: Optional identifier for the releaser

        Raises:
            ResourceError: If the resource is not from this pool
        """
        async with self._lock:
            # Find the pooled resource containing this resource
            pooled_resource = None
            for resource_id, pr in self._resources.items():
                if pr.resource is resource:
                    pooled_resource = pr
                    break

            if pooled_resource is None:
                raise ResourceError(f"Resource not found in pool {self.pool_id}")

            # Release the resource
            try:
                await pooled_resource.release(owner)
                self._available_resources.add(pooled_resource.resource_id)
                self._metrics.resource_released()

                # Notify waiters
                self._condition.notify_all()

                # Check if we should scale down
                await self._check_scaling()

            except Exception as e:
                logger.error(
                    f"Error releasing resource {pooled_resource.resource_id}: {e}"
                )
                raise ResourceError(
                    f"Error releasing resource to pool {self.pool_id}: {e}"
                ) from e

    async def _check_scaling(self) -> None:
        """Check if the pool should be scaled up or down."""
        if not self._auto_scaling_enabled:
            return

        # Calculate usage
        total_resources = len(self._resources)
        available_resources = len(self._available_resources)
        in_use_resources = total_resources - available_resources

        if total_resources == 0:
            usage_ratio = 0
        else:
            usage_ratio = in_use_resources / total_resources

        # Scale up if needed
        if usage_ratio >= self._scale_up_threshold and total_resources < self.max_size:
            try:
                await self._create_resource()
                logger.info(
                    f"Scaled up pool {self.pool_id} to {len(self._resources)} resources "
                    f"(usage: {usage_ratio:.2f})"
                )
            except Exception as e:
                logger.error(f"Failed to scale up pool {self.pool_id}: {e}")

        # Scale down if needed
        elif (
            usage_ratio <= self._scale_down_threshold
            and total_resources > self.min_size
        ):
            # Get excess idle resources
            excess_idle = available_resources - self.max_idle

            if excess_idle > 0:
                # Remove excess idle resources
                for _ in range(min(excess_idle, total_resources - self.min_size)):
                    if not self._available_resources:
                        break

                    resource_id = next(iter(self._available_resources))

                    try:
                        await self._remove_resource(resource_id)
                        logger.info(
                            f"Scaled down pool {self.pool_id} to {len(self._resources)} resources "
                            f"(usage: {usage_ratio:.2f})"
                        )
                    except Exception as e:
                        logger.error(f"Failed to scale down pool {self.pool_id}: {e}")

        # Update metrics
        self._metrics.update_size_stats(len(self._resources))

    async def _remove_resource(self, resource_id: str) -> None:
        """Remove a resource from the pool.

        Args:
            resource_id: ID of the resource to remove

        Raises:
            ResourceError: If the resource is not in the pool
        """
        if resource_id not in self._resources:
            raise ResourceError(
                f"Resource {resource_id} not found in pool {self.pool_id}"
            )

        if resource_id not in self._available_resources:
            raise ResourceError(f"Resource {resource_id} is not available for removal")

        # Remove from available resources
        self._available_resources.remove(resource_id)

        # Get the pooled resource
        pooled_resource = self._resources[resource_id]

        # Close the resource
        try:
            await pooled_resource.close()
        finally:
            # Remove from resources dict
            del self._resources[resource_id]
            self._metrics.resource_removed()

    async def close(self) -> None:
        """Close the pool and all resources."""
        async with self._lock:
            if self._closing:
                return

            self._closing = True

            # Close all resources
            for resource_id, pooled_resource in list(self._resources.items()):
                try:
                    await pooled_resource.close()
                except Exception as e:
                    logger.error(f"Error closing resource {resource_id}: {e}")

            # Clear resources
            self._resources.clear()
            self._available_resources.clear()

            logger.info(f"Closed resource pool {self.pool_id}")

    def set_auto_scaling(
        self,
        enabled: bool,
        scale_up_threshold: Optional[float] = None,
        scale_down_threshold: Optional[float] = None,
    ) -> None:
        """Configure auto-scaling for the pool.

        Args:
            enabled: Whether auto-scaling is enabled
            scale_up_threshold: Threshold for scaling up (0.0-1.0)
            scale_down_threshold: Threshold for scaling down (0.0-1.0)
        """
        self._auto_scaling_enabled = enabled

        if scale_up_threshold is not None:
            self._scale_up_threshold = max(0.0, min(1.0, scale_up_threshold))

        if scale_down_threshold is not None:
            self._scale_down_threshold = max(0.0, min(1.0, scale_down_threshold))

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for the pool and all resources.

        Returns:
            Dictionary of metrics
        """
        pool_metrics = self._metrics.get_metrics()

        # Add current stats
        pool_metrics.update(
            {
                "current_size": len(self._resources),
                "available_resources": len(self._available_resources),
                "in_use_resources": len(self._resources)
                - len(self._available_resources),
                "usage_ratio": (
                    (len(self._resources) - len(self._available_resources))
                    / len(self._resources)
                    if len(self._resources) > 0
                    else 0
                ),
                "auto_scaling_enabled": self._auto_scaling_enabled,
                "scale_up_threshold": self._scale_up_threshold,
                "scale_down_threshold": self._scale_down_threshold,
                "is_closing": self._closing,
            }
        )

        # Add resource metrics
        resource_metrics = {
            resource_id: pooled_resource.metrics.get_metrics()
            for resource_id, pooled_resource in self._resources.items()
        }

        return {
            "pool": pool_metrics,
            "resources": resource_metrics,
        }


class ResourcePoolManager:
    """Manager for resource pools."""

    def __init__(self) -> None:
        """Initialize the resource pool manager."""
        self._pools: Dict[str, ResourcePool] = {}
        self._lock = asyncio.Lock()

    async def create_pool(
        self,
        pool_id: str,
        resource_type: str,
        factory: Callable[[], Any],
        initial_size: int = 1,
        min_size: int = 1,
        max_size: int = 10,
        max_idle: int = 5,
        cleanup_func: Optional[Callable[[Any], Any]] = None,
        initialize: bool = True,
    ) -> ResourcePool:
        """Create a new resource pool.

        Args:
            pool_id: Unique identifier for the pool
            resource_type: Type of resources in the pool
            factory: Function to create new resources
            initial_size: Initial number of resources in the pool
            min_size: Minimum number of resources in the pool
            max_size: Maximum number of resources in the pool
            max_idle: Maximum number of idle resources to keep
            cleanup_func: Optional function to call for cleanup
            initialize: Whether to initialize the pool immediately

        Returns:
            The created resource pool

        Raises:
            ResourceError: If a pool with the same ID already exists
        """
        async with self._lock:
            if pool_id in self._pools:
                raise ResourceError(f"Resource pool {pool_id} already exists")

            pool = ResourcePool(
                pool_id=pool_id,
                resource_type=resource_type,
                factory=factory,
                initial_size=initial_size,
                min_size=min_size,
                max_size=max_size,
                max_idle=max_idle,
                cleanup_func=cleanup_func,
            )

            self._pools[pool_id] = pool

            if initialize:
                await pool.initialize()

            logger.info(
                f"Created resource pool {pool_id} "
                f"(type: {resource_type}, initial size: {initial_size})"
            )

            return pool

    async def get_pool(self, pool_id: str) -> ResourcePool:
        """Get a resource pool by ID.

        Args:
            pool_id: ID of the pool to get

        Returns:
            The resource pool

        Raises:
            ResourceError: If the pool does not exist
        """
        async with self._lock:
            pool = self._pools.get(pool_id)

            if pool is None:
                raise ResourceError(f"Resource pool {pool_id} does not exist")

            return pool

    async def get_or_create_pool(
        self,
        pool_id: str,
        resource_type: str,
        factory: Callable[[], Any],
        initial_size: int = 1,
        min_size: int = 1,
        max_size: int = 10,
        max_idle: int = 5,
        cleanup_func: Optional[Callable[[Any], Any]] = None,
        initialize: bool = True,
    ) -> ResourcePool:
        """Get a resource pool by ID, or create it if it doesn't exist.

        Args:
            pool_id: Unique identifier for the pool
            resource_type: Type of resources in the pool
            factory: Function to create new resources
            initial_size: Initial number of resources in the pool
            min_size: Minimum number of resources in the pool
            max_size: Maximum number of resources in the pool
            max_idle: Maximum number of idle resources to keep
            cleanup_func: Optional function to call for cleanup
            initialize: Whether to initialize the pool immediately

        Returns:
            The resource pool
        """
        async with self._lock:
            pool = self._pools.get(pool_id)

            if pool is None:
                pool = await self.create_pool(
                    pool_id=pool_id,
                    resource_type=resource_type,
                    factory=factory,
                    initial_size=initial_size,
                    min_size=min_size,
                    max_size=max_size,
                    max_idle=max_idle,
                    cleanup_func=cleanup_func,
                    initialize=initialize,
                )

            return pool

    async def remove_pool(self, pool_id: str) -> None:
        """Remove a resource pool.

        Args:
            pool_id: ID of the pool to remove

        Raises:
            ResourceError: If the pool does not exist
        """
        async with self._lock:
            pool = self._pools.get(pool_id)

            if pool is None:
                raise ResourceError(f"Resource pool {pool_id} does not exist")

            # Close the pool
            await pool.close()

            # Remove from pools dict
            del self._pools[pool_id]

            logger.info(f"Removed resource pool {pool_id}")

    async def close_all_pools(self) -> None:
        """Close all resource pools."""
        async with self._lock:
            for pool_id, pool in list(self._pools.items()):
                try:
                    await pool.close()
                except Exception as e:
                    logger.error(f"Error closing resource pool {pool_id}: {e}")

            # Clear pools
            self._pools.clear()

            logger.info("Closed all resource pools")

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all pools.

        Returns:
            Dictionary mapping pool IDs to metrics
        """
        return {pool_id: pool.get_metrics() for pool_id, pool in self._pools.items()}

    def count_pools(self) -> int:
        """Get the number of pools.

        Returns:
            Number of pools
        """
        return len(self._pools)

    def count_resources(self) -> int:
        """Get the total number of resources across all pools.

        Returns:
            Total number of resources
        """
        return sum(
            pool.get_metrics()["pool"]["current_size"] for pool in self._pools.values()
        )


# Global resource pool manager instance
_resource_pool_manager: Optional[ResourcePoolManager] = None


def get_resource_pool_manager() -> ResourcePoolManager:
    """Get the global resource pool manager.

    Returns:
        ResourcePoolManager instance
    """
    global _resource_pool_manager
    if _resource_pool_manager is None:
        _resource_pool_manager = ResourcePoolManager()

    return _resource_pool_manager


class PooledResourceContext(Generic[T]):
    """Context manager for pooled resources."""

    def __init__(
        self,
        pool: ResourcePool[T],
        owner: str = "unknown",
        timeout: Optional[float] = None,
    ) -> None:
        """Initialize context manager.

        Args:
            pool: Resource pool to acquire from
            owner: Identifier for the owner
            timeout: Optional timeout in seconds
        """
        self.pool = pool
        self.owner = owner
        self.timeout = timeout
        self.resource: Optional[T] = None

    async def __aenter__(self) -> T:
        """Acquire a resource.

        Returns:
            Resource from the pool
        """
        self.resource = await self.pool.acquire(self.owner, self.timeout)
        return self.resource

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Release the resource."""
        if self.resource is not None:
            await self.pool.release(self.resource, self.owner)
