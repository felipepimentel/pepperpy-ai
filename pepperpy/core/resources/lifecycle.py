"""Resource lifecycle module.

This module provides functionality for managing resource lifecycles.
"""

from collections.abc import Callable, Coroutine
from typing import Any

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ValidationError
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.resources.cleanup import ResourceCleaner
from pepperpy.resources.monitoring import ResourceMonitor
from pepperpy.resources.pool import ResourcePool
from pepperpy.resources.types import Resource


class ResourceLifecycle(Lifecycle):
    """Resource lifecycle manager."""

    def __init__(
        self,
        cleanup_interval: int = 300,  # 5 minutes
        monitor_interval: int = 60,  # 1 minute
        max_age: int = 3600,  # 1 hour
        max_retries: int = 3,
    ) -> None:
        """Initialize resource lifecycle.

        Args:
            cleanup_interval: Cleanup interval in seconds
            monitor_interval: Monitor interval in seconds
            max_age: Maximum resource age in seconds
            max_retries: Maximum retry attempts
        """
        super().__init__()
        self._state = ComponentState.CREATED
        self._resources: dict[str, Resource] = {}
        self._pools: dict[str, ResourcePool] = {}
        self._hooks: dict[
            str, list[Callable[[Resource], Coroutine[Any, Any, None]]]
        ] = {}

        # Initialize components
        self._cleaner = ResourceCleaner(
            cleanup_interval=cleanup_interval,
            max_age=max_age,
            max_retries=max_retries,
        )
        self._monitor = ResourceMonitor(
            monitor_interval=monitor_interval,
        )

    async def initialize(self) -> None:
        """Initialize lifecycle."""
        try:
            self._state = ComponentState.INITIALIZING

            # Initialize components
            await self._cleaner.initialize()
            await self._monitor.initialize()

            # Initialize pools
            for pool in self._pools.values():
                await pool.initialize()

            self._state = ComponentState.READY
            logger.info("Resource lifecycle initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize lifecycle: {e}")

    async def cleanup(self) -> None:
        """Clean up lifecycle."""
        try:
            self._state = ComponentState.CLEANING

            # Clean up pools
            for pool in self._pools.values():
                await pool.cleanup()

            # Clean up components
            await self._monitor.cleanup()
            await self._cleaner.cleanup()

            self._state = ComponentState.CLEANED
            logger.info("Resource lifecycle cleaned up")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up lifecycle: {e}")

    def register_pool(self, pool: ResourcePool) -> None:
        """Register resource pool.

        Args:
            pool: Resource pool to register

        Raises:
            ValidationError: If pool already exists
        """
        if pool.name in self._pools:
            raise ValidationError(f"Pool already exists: {pool.name}")
        self._pools[pool.name] = pool

    def unregister_pool(self, name: str) -> None:
        """Unregister resource pool.

        Args:
            name: Pool name

        Raises:
            ValidationError: If pool not found
        """
        if name not in self._pools:
            raise ValidationError(f"Pool not found: {name}")
        del self._pools[name]

    def register_hook(
        self,
        event: str,
        hook: Callable[[Resource], Coroutine[Any, Any, None]],
    ) -> None:
        """Register lifecycle hook.

        Args:
            event: Lifecycle event
            hook: Hook function
        """
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(hook)

    def unregister_hook(
        self,
        event: str,
        hook: Callable[[Resource], Coroutine[Any, Any, None]],
    ) -> None:
        """Unregister lifecycle hook.

        Args:
            event: Lifecycle event
            hook: Hook function
        """
        if event in self._hooks:
            self._hooks[event].remove(hook)
            if not self._hooks[event]:
                del self._hooks[event]

    async def register_resource(self, resource: Resource) -> None:
        """Register resource.

        Args:
            resource: Resource to register
        """
        self._resources[resource.id] = resource
        self._cleaner.register_resource(resource)
        self._monitor.register_resource(resource)
        await self._notify_hooks("register", resource)

    async def unregister_resource(self, resource_id: str) -> None:
        """Unregister resource.

        Args:
            resource_id: Resource ID
        """
        if resource_id in self._resources:
            resource = self._resources[resource_id]
            del self._resources[resource_id]
            self._cleaner.unregister_resource(resource_id)
            self._monitor.unregister_resource(resource_id)
            await self._notify_hooks("unregister", resource)

    async def acquire_resource(self, pool_name: str, resource_id: str) -> Resource:
        """Acquire resource from pool.

        Args:
            pool_name: Pool name
            resource_id: Resource ID

        Returns:
            Resource instance

        Raises:
            ValidationError: If pool not found
        """
        if pool_name not in self._pools:
            raise ValidationError(f"Pool not found: {pool_name}")
        resource = await self._pools[pool_name].acquire(resource_id)
        await self._notify_hooks("acquire", resource)
        return resource

    async def release_resource(self, pool_name: str, resource_id: str) -> None:
        """Release resource to pool.

        Args:
            pool_name: Pool name
            resource_id: Resource ID

        Raises:
            ValidationError: If pool not found
        """
        if pool_name not in self._pools:
            raise ValidationError(f"Pool not found: {pool_name}")
        if resource_id in self._resources:
            resource = self._resources[resource_id]
            await self._pools[pool_name].release(resource_id)
            await self._notify_hooks("release", resource)

    async def _notify_hooks(self, event: str, resource: Resource) -> None:
        """Notify lifecycle hooks.

        Args:
            event: Lifecycle event
            resource: Resource instance
        """
        if event in self._hooks:
            for hook in self._hooks[event]:
                try:
                    await hook(resource)
                except Exception as e:
                    logger.error(
                        f"Hook failed for event {event}: {e}",
                        extra={
                            "resource_id": resource.id,
                            "event": event,
                        },
                        exc_info=True,
                    )

    def get_metrics(self) -> dict[str, Any]:
        """Get resource metrics.

        Returns:
            Dictionary containing:
            - total_resources: Total number of resources
            - state_counts: Resource state counts
            - pool_stats: Pool statistics
            - resource_stats: Resource statistics
        """
        metrics = self._monitor.get_metrics()
        pool_stats = {
            pool.name: {
                "total": len(pool._resources),
                "available": len(pool._available),
                "in_use": len(pool._in_use),
            }
            for pool in self._pools.values()
        }
        metrics["pool_stats"] = pool_stats
        return metrics


# Export public API
__all__ = ["ResourceLifecycle"]
