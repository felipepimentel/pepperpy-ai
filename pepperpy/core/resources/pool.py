"""Resource pool module.

This module provides resource pool implementations for managing resources.
"""

import asyncio
from typing import Callable, Dict, Generic, Optional, TypeVar

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ValidationError
from pepperpy.core.metrics import Counter, Gauge, Histogram
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.resources.types import Resource

# Type variables
T = TypeVar("T", bound=Resource)


class ResourcePool(Lifecycle, Generic[T]):
    """Base resource pool."""

    def __init__(
        self,
        name: str,
        resource_type: type[T],
        factory: Callable[[], T],
        min_size: int = 1,
        max_size: int = 10,
        scale_up_threshold: float = 0.8,  # Scale up when 80% utilized
        scale_down_threshold: float = 0.2,  # Scale down when 20% utilized
    ) -> None:
        """Initialize resource pool.

        Args:
            name: Pool name
            resource_type: Resource type
            factory: Resource factory function
            min_size: Minimum pool size
            max_size: Maximum pool size
            scale_up_threshold: Utilization threshold for scaling up
            scale_down_threshold: Utilization threshold for scaling down

        """
        super().__init__()
        self.name = name
        self.resource_type = resource_type
        self._factory = factory
        self._min_size = min_size
        self._max_size = max_size
        self._scale_up_threshold = scale_up_threshold
        self._scale_down_threshold = scale_down_threshold
        self._state = ComponentState.CREATED
        self._resources: Dict[str, T] = {}
        self._available: set[str] = set()
        self._in_use: set[str] = set()
        self._lock = asyncio.Lock()
        self._scaling_task: Optional[asyncio.Task] = None

        # Initialize metrics
        self._pool_size = Gauge(
            f"resource_pool_{name}_size",
            "Current pool size",
        )
        self._in_use_count = Gauge(
            f"resource_pool_{name}_in_use",
            "Number of resources in use",
        )
        self._utilization = Gauge(
            f"resource_pool_{name}_utilization",
            "Pool utilization percentage",
        )
        self._scale_ops = Counter(
            f"resource_pool_{name}_scale_ops",
            "Number of scaling operations",
        )
        self._acquire_time = Histogram(
            f"resource_pool_{name}_acquire_time",
            "Time to acquire a resource",
        )

    async def initialize(self) -> None:
        """Initialize pool."""
        try:
            self._state = ComponentState.INITIALIZING
            await self._initialize_pool()
            self._scaling_task = asyncio.create_task(self._scaling_loop())
            self._state = ComponentState.READY
            logger.info(
                f"Resource pool initialized: {self.name}",
                extra={
                    "name": self.name,
                    "min_size": self._min_size,
                    "max_size": self._max_size,
                },
            )
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize pool: {e}") from e

    async def cleanup(self) -> None:
        """Clean up pool."""
        try:
            self._state = ComponentState.CLEANING
            if self._scaling_task:
                self._scaling_task.cancel()
                try:
                    await self._scaling_task
                except asyncio.CancelledError:
                    pass
            await self._cleanup_pool()
            self._state = ComponentState.CLEANED
            logger.info(f"Resource pool cleaned up: {self.name}")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up pool: {e}") from e

    async def _initialize_pool(self) -> None:
        """Initialize pool with minimum resources."""
        async with self._lock:
            for _ in range(self._min_size):
                resource = self._factory()
                await resource.load()
                self._resources[resource.id] = resource
                self._available.add(resource.id)
                self._pool_size.inc()

    async def _cleanup_pool(self) -> None:
        """Clean up all resources in pool."""
        async with self._lock:
            for resource in self._resources.values():
                try:
                    await resource.delete()
                except Exception as e:
                    logger.error(
                        f"Failed to delete resource {resource.id}: {e}",
                        extra={"resource_id": resource.id},
                        exc_info=True,
                    )
            self._resources.clear()
            self._available.clear()
            self._in_use.clear()
            self._pool_size.set(0)
            self._in_use_count.set(0)
            self._utilization.set(0)

    async def acquire(self, wait: bool = True) -> T:
        """Acquire a resource from the pool.

        Args:
            wait: Whether to wait for a resource if none available

        Returns:
            Resource instance

        Raises:
            ValidationError: If no resources available and wait=False

        """
        start_time = asyncio.get_event_loop().time()
        try:
            async with self._lock:
                while True:
                    # Try to get an available resource
                    if self._available:
                        resource_id = next(iter(self._available))
                        self._available.remove(resource_id)
                        self._in_use.add(resource_id)
                        self._update_metrics()
                        return self._resources[resource_id]

                    # No resources available
                    if not wait:
                        raise ValidationError("No resources available")

                    # Wait for a resource to become available
                    await asyncio.sleep(0.1)
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            self._acquire_time.observe(duration)

    async def release(self, resource: T) -> None:
        """Release a resource back to the pool.

        Args:
            resource: Resource to release

        Raises:
            ValidationError: If resource not found or not in use

        """
        async with self._lock:
            if resource.id not in self._resources:
                raise ValidationError(f"Resource not found: {resource.id}")
            if resource.id not in self._in_use:
                raise ValidationError(f"Resource not in use: {resource.id}")

            self._in_use.remove(resource.id)
            self._available.add(resource.id)
            self._update_metrics()

    async def _scaling_loop(self) -> None:
        """Run scaling loop to adjust pool size."""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                await self._check_scaling()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scaling loop: {e}", exc_info=True)

    async def _check_scaling(self) -> None:
        """Check and adjust pool size based on utilization."""
        async with self._lock:
            total = len(self._resources)
            if total == 0:
                return

            utilization = len(self._in_use) / total

            # Scale up if needed
            if utilization >= self._scale_up_threshold and total < self._max_size:
                try:
                    resource = self._factory()
                    await resource.load()
                    self._resources[resource.id] = resource
                    self._available.add(resource.id)
                    self._pool_size.inc()
                    self._scale_ops.inc({"operation": "scale_up"})
                    logger.info(
                        f"Scaled up pool {self.name}",
                        extra={
                            "name": self.name,
                            "current_size": len(self._resources),
                            "utilization": utilization,
                        },
                    )
                except Exception as e:
                    logger.error(f"Failed to scale up pool: {e}", exc_info=True)

            # Scale down if needed
            elif (
                utilization <= self._scale_down_threshold
                and total > self._min_size
                and self._available
            ):
                try:
                    resource_id = next(iter(self._available))
                    resource = self._resources[resource_id]
                    await resource.delete()
                    del self._resources[resource_id]
                    self._available.remove(resource_id)
                    self._pool_size.dec()
                    self._scale_ops.inc({"operation": "scale_down"})
                    logger.info(
                        f"Scaled down pool {self.name}",
                        extra={
                            "name": self.name,
                            "current_size": len(self._resources),
                            "utilization": utilization,
                        },
                    )
                except Exception as e:
                    logger.error(f"Failed to scale down pool: {e}", exc_info=True)

    def _update_metrics(self) -> None:
        """Update pool metrics."""
        total = len(self._resources)
        in_use = len(self._in_use)
        utilization = in_use / total if total > 0 else 0

        self._pool_size.set(total)
        self._in_use_count.set(in_use)
        self._utilization.set(utilization)


# Export public API
__all__ = ["ResourcePool"]
