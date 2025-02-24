"""Resource cleanup module.

This module provides functionality for cleaning up resources.
"""

import asyncio
from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta
from typing import Any

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ValidationError
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.resources.types import Resource, ResourceState


class ResourceCleaner(Lifecycle):
    """Resource cleaner."""

    def __init__(
        self,
        cleanup_interval: int = 300,  # 5 minutes
        max_age: int = 3600,  # 1 hour
        max_retries: int = 3,
    ) -> None:
        """Initialize resource cleaner.

        Args:
            cleanup_interval: Cleanup interval in seconds
            max_age: Maximum resource age in seconds
            max_retries: Maximum cleanup retry attempts
        """
        super().__init__()
        self._cleanup_interval = cleanup_interval
        self._max_age = max_age
        self._max_retries = max_retries
        self._state = ComponentState.CREATED
        self._resources: dict[str, Resource] = {}
        self._cleanup_hooks: dict[
            str, Callable[[Resource], Coroutine[Any, Any, None]]
        ] = {}
        self._task: asyncio.Task[None] | None = None

    async def initialize(self) -> None:
        """Initialize cleaner."""
        try:
            self._state = ComponentState.INITIALIZING
            self._task = asyncio.create_task(self._cleanup_loop())
            self._state = ComponentState.READY
            logger.info("Resource cleaner initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize cleaner: {e}")

    async def cleanup(self) -> None:
        """Clean up cleaner."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            await self._cleanup_all()
            self._state = ComponentState.CLEANED
            logger.info("Resource cleaner cleaned up")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up cleaner: {e}")

    def register_resource(self, resource: Resource) -> None:
        """Register resource for cleanup.

        Args:
            resource: Resource to register
        """
        self._resources[resource.id] = resource
        logger.debug(f"Registered resource for cleanup: {resource.id}")

    def unregister_resource(self, resource_id: str) -> None:
        """Unregister resource from cleanup.

        Args:
            resource_id: Resource ID
        """
        if resource_id in self._resources:
            del self._resources[resource_id]
            logger.debug(f"Unregistered resource from cleanup: {resource_id}")

    def register_cleanup_hook(
        self,
        resource_type: str,
        hook: Callable[[Resource], Coroutine[Any, Any, None]],
    ) -> None:
        """Register cleanup hook.

        Args:
            resource_type: Resource type
            hook: Cleanup hook function
        """
        self._cleanup_hooks[resource_type] = hook
        logger.debug(f"Registered cleanup hook for type: {resource_type}")

    def unregister_cleanup_hook(self, resource_type: str) -> None:
        """Unregister cleanup hook.

        Args:
            resource_type: Resource type
        """
        if resource_type in self._cleanup_hooks:
            del self._cleanup_hooks[resource_type]
            logger.debug(f"Unregistered cleanup hook for type: {resource_type}")

    async def _cleanup_loop(self) -> None:
        """Run cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

    async def _cleanup_expired(self) -> None:
        """Clean up expired resources."""
        now = datetime.utcnow()
        expired = [
            resource
            for resource in self._resources.values()
            if (
                resource.state != ResourceState.DELETED
                and resource.metadata.expires_at
                and resource.metadata.expires_at <= now
            )
            or (resource.metadata.created_at + timedelta(seconds=self._max_age) <= now)
        ]

        for resource in expired:
            try:
                await self._cleanup_resource(resource)
            except Exception as e:
                logger.error(
                    f"Failed to clean up resource {resource.id}: {e}",
                    exc_info=True,
                )

    async def _cleanup_all(self) -> None:
        """Clean up all resources."""
        for resource in self._resources.values():
            try:
                await self._cleanup_resource(resource)
            except Exception as e:
                logger.error(
                    f"Failed to clean up resource {resource.id}: {e}",
                    exc_info=True,
                )

    async def _cleanup_resource(self, resource: Resource) -> None:
        """Clean up resource.

        Args:
            resource: Resource to clean up
        """
        hook = self._cleanup_hooks.get(str(resource.type))
        if hook:
            try:
                await hook(resource)
            except Exception as e:
                logger.error(
                    f"Cleanup hook failed for resource {resource.id}: {e}",
                    exc_info=True,
                )

        retries = 0
        while retries < self._max_retries:
            try:
                await resource.delete()
                self.unregister_resource(resource.id)
                logger.info(f"Cleaned up resource: {resource.id}")
                break
            except Exception as e:
                retries += 1
                if retries >= self._max_retries:
                    logger.error(
                        f"Failed to clean up resource {resource.id} after {retries} retries: {e}",
                        exc_info=True,
                    )
                else:
                    logger.warning(
                        f"Retry {retries} cleaning up resource {resource.id}: {e}"
                    )
                    await asyncio.sleep(1)


# Export public API
__all__ = ["ResourceCleaner"]
