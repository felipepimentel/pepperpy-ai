"""Resource pool module.

This module provides resource pool implementations for managing resources.
"""

import asyncio
from typing import Generic, TypeVar

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ValidationError
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.resources.types import Resource

# Type variables
T = TypeVar("T", bound=Resource)


class ResourcePool(Lifecycle, Generic[T]):
    """Base resource pool."""

    def __init__(self, name: str, resource_type: type[T]) -> None:
        """Initialize resource pool.

        Args:
            name: Pool name
            resource_type: Resource type
        """
        super().__init__()
        self.name = name
        self.resource_type = resource_type
        self._state = ComponentState.CREATED
        self._resources: dict[str, T] = {}
        self._available: set[str] = set()
        self._in_use: set[str] = set()
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize pool."""
        try:
            self._state = ComponentState.INITIALIZING
            await self._initialize_pool()
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize pool: {e}")

    async def cleanup(self) -> None:
        """Clean up pool."""
        try:
            self._state = ComponentState.CLEANING
            await self._cleanup_pool()
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up pool: {e}")

    async def _initialize_pool(self) -> None:
        """Initialize pool implementation."""
        pass

    async def _cleanup_pool(self) -> None:
        """Clean up pool implementation."""
        pass

    async def acquire(self, resource_id: str) -> T:
        """Acquire resource.

        Args:
            resource_id: Resource ID

        Returns:
            Resource instance

        Raises:
            ValidationError: If resource not found or not available
        """
        async with self._lock:
            if resource_id not in self._resources:
                raise ValidationError(f"Resource not found: {resource_id}")
            if resource_id not in self._available:
                raise ValidationError(f"Resource not available: {resource_id}")

            self._available.remove(resource_id)
            self._in_use.add(resource_id)
            return self._resources[resource_id]

    async def release(self, resource_id: str) -> None:
        """Release resource.

        Args:
            resource_id: Resource ID

        Raises:
            ValidationError: If resource not found or not in use
        """
        async with self._lock:
            if resource_id not in self._resources:
                raise ValidationError(f"Resource not found: {resource_id}")
            if resource_id not in self._in_use:
                raise ValidationError(f"Resource not in use: {resource_id}")

            self._in_use.remove(resource_id)
            self._available.add(resource_id)

    async def add_resource(self, resource: T) -> None:
        """Add resource to pool.

        Args:
            resource: Resource to add

        Raises:
            ValidationError: If resource already exists
        """
        async with self._lock:
            if resource.id in self._resources:
                raise ValidationError(f"Resource already exists: {resource.id}")

            self._resources[resource.id] = resource
            self._available.add(resource.id)

    async def remove_resource(self, resource_id: str) -> None:
        """Remove resource from pool.

        Args:
            resource_id: Resource ID

        Raises:
            ValidationError: If resource not found or in use
        """
        async with self._lock:
            if resource_id not in self._resources:
                raise ValidationError(f"Resource not found: {resource_id}")
            if resource_id in self._in_use:
                raise ValidationError(f"Resource in use: {resource_id}")

            del self._resources[resource_id]
            self._available.remove(resource_id)


class MemoryResourcePool(ResourcePool[T]):
    """Memory-based resource pool."""

    def __init__(self, name: str, resource_type: type[T]) -> None:
        """Initialize memory resource pool.

        Args:
            name: Pool name
            resource_type: Resource type
        """
        super().__init__(name, resource_type)
        self._max_size = 1000
        self._max_memory = 1024 * 1024 * 1024  # 1GB

    async def _initialize_pool(self) -> None:
        """Initialize memory pool."""
        logger.info(
            "Initializing memory pool",
            extra={
                "name": self.name,
                "max_size": self._max_size,
                "max_memory": self._max_memory,
            },
        )

    async def _cleanup_pool(self) -> None:
        """Clean up memory pool."""
        logger.info(
            "Cleaning up memory pool",
            extra={
                "name": self.name,
                "resources": len(self._resources),
            },
        )
        self._resources.clear()
        self._available.clear()
        self._in_use.clear()


class AsyncResourcePool(ResourcePool[T]):
    """Asynchronous resource pool."""

    def __init__(
        self,
        name: str,
        resource_type: type[T],
        max_concurrent: int = 10,
    ) -> None:
        """Initialize async resource pool.

        Args:
            name: Pool name
            resource_type: Resource type
            max_concurrent: Maximum concurrent resources
        """
        super().__init__(name, resource_type)
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def acquire(self, resource_id: str) -> T:
        """Acquire resource with concurrency control.

        Args:
            resource_id: Resource ID

        Returns:
            Resource instance

        Raises:
            ValidationError: If resource not found or not available
        """
        async with self._semaphore:
            return await super().acquire(resource_id)


# Export public API
__all__ = [
    "AsyncResourcePool",
    "MemoryResourcePool",
    "ResourcePool",
]
