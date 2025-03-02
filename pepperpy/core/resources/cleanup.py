"""Resource cleanup module.

This module provides automatic cleanup functionality for resources.
"""

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ValidationError
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.resources.types import Resource


class CleanupScheduler(Lifecycle):
    """Resource cleanup scheduler."""

    def __init__(
        self,
        default_ttl: int = 3600,  # 1 hour
        cleanup_interval: int = 300,  # 5 minutes
    ) -> None:
        """Initialize cleanup scheduler.

        Args:
            default_ttl: Default time-to-live in seconds
            cleanup_interval: Cleanup check interval in seconds
        """
        super().__init__()
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._state = ComponentState.CREATED
        self._resources: dict[str, Resource] = {}
        self._expiry_times: dict[str, datetime] = {}
        self._cleanup_hooks: dict[str, Callable[[Resource], Any]] = {}
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize scheduler."""
        try:
            self._state = ComponentState.INITIALIZING
            self._task = asyncio.create_task(self._cleanup_loop())
            self._state = ComponentState.READY
            logger.info("Cleanup scheduler initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize scheduler: {e}") from e

    async def cleanup(self) -> None:
        """Clean up scheduler."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            self._state = ComponentState.CLEANED
            logger.info("Cleanup scheduler cleaned up")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up scheduler: {e}") from e

    async def schedule(
        self,
        resource: Resource,
        ttl: int | None = None,
        cleanup_hook: Callable[[Resource], Any] | None = None,
    ) -> None:
        """Schedule resource for cleanup.

        Args:
            resource: Resource to schedule
            ttl: Time-to-live in seconds (uses default if None)
            cleanup_hook: Optional cleanup hook function
        """
        async with self._lock:
            ttl = ttl or self._default_ttl
            expiry_time = datetime.utcnow() + timedelta(seconds=ttl)

            self._resources[resource.id] = resource
            self._expiry_times[resource.id] = expiry_time
            if cleanup_hook:
                self._cleanup_hooks[resource.id] = cleanup_hook

            logger.debug(
                f"Scheduled resource for cleanup: {resource.id}",
                extra={
                    "resource_id": resource.id,
                    "ttl": ttl,
                    "expiry_time": expiry_time.isoformat(),
                },
            )

    async def unschedule(self, resource_id: str) -> None:
        """Unschedule resource from cleanup.

        Args:
            resource_id: Resource ID
        """
        async with self._lock:
            if resource_id in self._resources:
                del self._resources[resource_id]
                del self._expiry_times[resource_id]
                self._cleanup_hooks.pop(resource_id, None)
                logger.debug(f"Unscheduled resource from cleanup: {resource_id}")

    async def _cleanup_loop(self) -> None:
        """Run cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._check_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

    async def _check_expired(self) -> None:
        """Check and clean up expired resources."""
        now = datetime.utcnow()
        expired_ids = []

        async with self._lock:
            # Find expired resources
            for resource_id, expiry_time in self._expiry_times.items():
                if now >= expiry_time:
                    expired_ids.append(resource_id)

            # Clean up expired resources
            for resource_id in expired_ids:
                resource = self._resources[resource_id]
                try:
                    # Call cleanup hook if exists
                    if resource_id in self._cleanup_hooks:
                        await self._cleanup_hooks[resource_id](resource)

                    # Delete resource
                    await resource.delete()

                    # Remove from tracking
                    del self._resources[resource_id]
                    del self._expiry_times[resource_id]
                    self._cleanup_hooks.pop(resource_id, None)

                    logger.info(
                        f"Cleaned up expired resource: {resource_id}",
                        extra={"resource_id": resource_id},
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to clean up resource {resource_id}: {e}",
                        extra={"resource_id": resource_id},
                        exc_info=True,
                    )


# Export public API
__all__ = ["CleanupScheduler"]
