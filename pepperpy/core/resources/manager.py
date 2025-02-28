"""Resource manager implementation.

This module provides the resource manager functionality:
- Resource allocation and deallocation
- Resource lifecycle management
- Resource monitoring and metrics
"""

import asyncio
from datetime import datetime
from typing import Any, Optional, TypeVar

from pydantic import BaseModel, Field

from pepperpy.core.common.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.monitoring.metrics import Counter, Gauge, MetricsManager
from pepperpy.resources.base import Resource, ResourceConfig

# Type variables
T = TypeVar("T", bound=Resource)


class ResourceManagerConfig(BaseModel):
    """Configuration for resource manager.

    Attributes:
        max_resources: Maximum number of resources
        cleanup_interval: Resource cleanup interval in seconds
        metrics_enabled: Whether metrics are enabled
    """

    max_resources: int = Field(default=1000, description="Maximum number of resources")
    cleanup_interval: float = Field(
        default=60.0, description="Resource cleanup interval in seconds"
    )
    metrics_enabled: bool = Field(
        default=True, description="Whether metrics are enabled"
    )


class ResourceManager(Lifecycle):
    """Resource manager implementation.

    This class handles resource allocation, lifecycle management,
    and monitoring across the framework.
    """

    _instance: Optional["ResourceManager"] = None

    def __init__(self, config: ResourceManagerConfig | None = None) -> None:
        """Initialize resource manager.

        Args:
            config: Optional resource manager configuration
        """
        super().__init__()
        self.config = config or ResourceManagerConfig()
        self._resources: dict[str, Resource] = {}
        self._resource_types: dict[str, type[Resource]] = {}
        self._state = ComponentState.UNREGISTERED
        self._cleanup_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._metrics = MetricsManager.get_instance()

        # Metrics
        self._total_resources: Gauge | None = None
        self._allocated_resources: Gauge | None = None
        self._in_use_resources: Gauge | None = None
        self._allocation_errors: Counter | None = None

    @classmethod
    def get_instance(cls) -> "ResourceManager":
        """Get resource manager instance.

        Returns:
            ResourceManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize resource manager."""
        try:
            # Create metrics
            if self.config.metrics_enabled:
                self._total_resources = await self._metrics.create_gauge(
                    "resources_total",
                    "Total number of resources",
                )
                self._allocated_resources = await self._metrics.create_gauge(
                    "resources_allocated",
                    "Number of allocated resources",
                )
                self._in_use_resources = await self._metrics.create_gauge(
                    "resources_in_use",
                    "Number of resources in use",
                )
                self._allocation_errors = await self._metrics.create_counter(
                    "resource_allocation_errors_total",
                    "Total number of resource allocation errors",
                )

            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            self._state = ComponentState.RUNNING
            logger.info("Resource manager initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize resource manager: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resource manager."""
        try:
            # Cancel cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

            # Clean up resources
            resources = list(self._resources.values())
            for resource in resources:
                try:
                    await resource.cleanup()
                except Exception as e:
                    logger.error(f"Failed to cleanup resource {resource.name}: {e}")

            self._resources.clear()
            self._resource_types.clear()
            self._state = ComponentState.UNREGISTERED
            logger.info("Resource manager cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup resource manager: {e}")
            raise

    def register_resource_type(self, resource_type: type[Resource]) -> None:
        """Register resource type.

        Args:
            resource_type: Resource type to register
        """
        self._resource_types[resource_type.__name__] = resource_type

    async def allocate(
        self, resource_type: str, name: str | None = None, **kwargs: Any
    ) -> Resource:
        """Allocate resource.

        Args:
            resource_type: Type of resource to allocate
            name: Optional resource name
            **kwargs: Additional resource configuration

        Returns:
            Allocated resource

        Raises:
            ValueError: If resource type not registered
            RuntimeError: If maximum resources reached
        """
        async with self._lock:
            # Check resource type
            if resource_type not in self._resource_types:
                raise ValueError(f"Resource type not registered: {resource_type}")

            # Check resource limit
            if len(self._resources) >= self.config.max_resources:
                if self._allocation_errors:
                    await self._allocation_errors.inc()
                raise RuntimeError("Maximum resources reached")

            try:
                # Create resource
                resource_class = self._resource_types[resource_type]
                config = ResourceConfig(
                    name=name or f"{resource_type}_{len(self._resources)}",
                    type=resource_type,
                    **kwargs,
                )
                resource = resource_class(config)

                # Initialize and allocate
                await resource.initialize()
                await resource.allocate()

                # Register resource
                self._resources[resource.name] = resource

                # Update metrics
                if self._total_resources:
                    await self._total_resources.inc()
                if self._allocated_resources:
                    await self._allocated_resources.inc()

                return resource

            except Exception as e:
                if self._allocation_errors:
                    await self._allocation_errors.inc()
                logger.error(f"Failed to allocate resource: {e}")
                raise

    async def release(self, resource: Resource) -> None:
        """Release resource.

        Args:
            resource: Resource to release
        """
        async with self._lock:
            if resource.name not in self._resources:
                return

            try:
                await resource.release()
                await resource.cleanup()
                del self._resources[resource.name]

                # Update metrics
                if self._total_resources:
                    await self._total_resources.dec()
                if self._allocated_resources:
                    await self._allocated_resources.dec()
                if resource.is_in_use() and self._in_use_resources:
                    await self._in_use_resources.dec()

            except Exception as e:
                logger.error(f"Failed to release resource {resource.name}: {e}")
                raise

    def get_resource(self, name: str) -> Resource | None:
        """Get resource by name.

        Args:
            name: Resource name

        Returns:
            Resource if found, None otherwise
        """
        return self._resources.get(name)

    def get_resources_by_type(self, resource_type: str) -> list[Resource]:
        """Get resources by type.

        Args:
            resource_type: Resource type

        Returns:
            List of resources of specified type
        """
        return [r for r in self._resources.values() if r.type == resource_type]

    def get_all_resources(self) -> list[Resource]:
        """Get all resources.

        Returns:
            List of all resources
        """
        return list(self._resources.values())

    async def _cleanup_loop(self) -> None:
        """Resource cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_unused_resources()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(1.0)  # Back off on error

    async def _cleanup_unused_resources(self) -> None:
        """Clean up unused resources."""
        async with self._lock:
            now = datetime.utcnow()
            resources = list(self._resources.values())

            for resource in resources:
                try:
                    # Skip resources in use
                    if resource.is_in_use():
                        continue

                    # Check if resource has been unused for too long
                    if (
                        resource.state.last_used
                        and (now - resource.state.last_used).total_seconds()
                        > self.config.cleanup_interval
                    ):
                        await self.release(resource)

                except Exception as e:
                    logger.error(f"Failed to cleanup resource {resource.name}: {e}")

    async def get_metrics(self) -> dict[str, Any]:
        """Get resource metrics.

        Returns:
            Dictionary containing resource metrics
        """
        metrics = {
            "total_resources": len(self._resources),
            "allocated_resources": len([
                r for r in self._resources.values() if r.is_allocated()
            ]),
            "in_use_resources": len([
                r for r in self._resources.values() if r.is_in_use()
            ]),
        }

        # Add metrics by type
        for resource_type in self._resource_types:
            resources = self.get_resources_by_type(resource_type)
            metrics[f"{resource_type}_total"] = len(resources)
            metrics[f"{resource_type}_allocated"] = len([
                r for r in resources if r.is_allocated()
            ])
            metrics[f"{resource_type}_in_use"] = len([
                r for r in resources if r.is_in_use()
            ])

        return metrics
