"""Asynchronous resource cleanup scheduling for PepperPy plugins.

This module provides utilities for scheduling resource cleanup operations,
including delayed cleanup, scheduled cleanup, and cleanup prioritization.
"""

import asyncio
import heapq
import time
import traceback
import weakref
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union

from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type variables
T = TypeVar("T")
CleanupFunc = Callable[[Any], Union[None, asyncio.Future[None]]]


class CleanupPriority(IntEnum):
    """Priority levels for resource cleanup."""

    # Critical resources that must be cleaned up immediately
    CRITICAL = 100

    # High priority resources that should be cleaned up soon
    HIGH = 75

    # Normal priority resources
    NORMAL = 50

    # Low priority resources that can be cleaned up later
    LOW = 25

    # Background resources that can be cleaned up when idle
    BACKGROUND = 0


@dataclass(order=True)
class ScheduledCleanup:
    """Scheduled cleanup operation."""

    # When to perform the cleanup (priority queue sort key)
    due_time: float

    # Priority for this cleanup (secondary sort key)
    priority: CleanupPriority = field(default=CleanupPriority.NORMAL)

    # Resource to clean up
    resource: Any = field(compare=False)

    # Function to call for cleanup
    cleanup_func: Optional[CleanupFunc] = field(compare=False, default=None)

    # Description of the resource (for logging)
    description: str = field(compare=False, default="")

    # Whether this is a retry
    is_retry: bool = field(compare=False, default=False)

    # Number of retries attempted
    retry_count: int = field(compare=False, default=0)

    # Maximum number of retries
    max_retries: int = field(compare=False, default=3)

    # Resource ID (for cancellation)
    resource_id: str = field(compare=False, default="")


class CleanupScheduler:
    """Scheduler for asynchronous resource cleanup.

    This class manages scheduling and execution of resource cleanup operations.
    """

    def __init__(
        self,
        max_concurrent_cleanups: int = 5,
        check_interval: float = 1.0,
        default_max_retries: int = 3,
        retry_delay: float = 5.0,
    ) -> None:
        """Initialize the cleanup scheduler.

        Args:
            max_concurrent_cleanups: Maximum number of concurrent cleanup operations
            check_interval: Interval in seconds to check for due cleanups
            default_max_retries: Default maximum number of retries for failed cleanups
            retry_delay: Delay in seconds before retrying a failed cleanup
        """
        self.max_concurrent_cleanups = max_concurrent_cleanups
        self.check_interval = check_interval
        self.default_max_retries = default_max_retries
        self.retry_delay = retry_delay

        self._cleanup_queue: List[ScheduledCleanup] = []
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent_cleanups)
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._active_cleanups: Set[str] = set()
        self._resource_refs: Dict[str, weakref.ref[Any]] = {}

    def start(self) -> None:
        """Start the cleanup scheduler."""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

        logger.debug("Cleanup scheduler started")

    def stop(self) -> None:
        """Stop the cleanup scheduler."""
        self._running = False

        if self._scheduler_task:
            self._scheduler_task.cancel()
            self._scheduler_task = None

        logger.debug("Cleanup scheduler stopped")

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop for processing cleanup operations."""
        try:
            while self._running:
                # Process due cleanups
                await self._process_due_cleanups()

                # Sleep until next check
                await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.debug("Cleanup scheduler task cancelled")
        except Exception as e:
            logger.error(f"Error in cleanup scheduler: {e}")
            logger.debug(traceback.format_exc())

    async def _process_due_cleanups(self) -> None:
        """Process all due cleanup operations."""
        now = time.time()
        due_cleanups = []

        async with self._lock:
            # Find all due cleanups
            while self._cleanup_queue and self._cleanup_queue[0].due_time <= now:
                cleanup = heapq.heappop(self._cleanup_queue)

                # Check if resource still exists (if using weak reference)
                resource_id = cleanup.resource_id
                if resource_id in self._resource_refs:
                    ref = self._resource_refs[resource_id]
                    resource = ref()

                    if resource is None:
                        # Resource has been garbage collected, skip cleanup
                        logger.debug(
                            f"Resource {cleanup.description} has been garbage collected, skipping cleanup"
                        )
                        continue

                    # Update resource reference in cleanup
                    cleanup.resource = resource

                due_cleanups.append(cleanup)

        # Process due cleanups
        for cleanup in due_cleanups:
            # Skip if resource ID is already being cleaned up
            if cleanup.resource_id and cleanup.resource_id in self._active_cleanups:
                continue

            # Schedule cleanup task
            asyncio.create_task(self._perform_cleanup(cleanup))

    async def _perform_cleanup(self, cleanup: ScheduledCleanup) -> None:
        """Perform a cleanup operation.

        Args:
            cleanup: Cleanup operation to perform
        """
        # Track active cleanup
        if cleanup.resource_id:
            self._active_cleanups.add(cleanup.resource_id)

        try:
            # Acquire semaphore to limit concurrent cleanups
            async with self._semaphore:
                logger.debug(f"Cleaning up resource: {cleanup.description}")

                try:
                    # Call cleanup function if provided
                    if cleanup.cleanup_func:
                        result = cleanup.cleanup_func(cleanup.resource)

                        # Handle coroutine result
                        if asyncio.isfuture(result) or asyncio.iscoroutine(result):
                            await result
                    else:
                        # Try standard cleanup methods
                        resource = cleanup.resource

                        if hasattr(resource, "cleanup") and callable(resource.cleanup):
                            cleanup_method = resource.cleanup

                            if asyncio.iscoroutinefunction(cleanup_method):
                                await cleanup_method()
                            else:
                                cleanup_method()

                        elif hasattr(resource, "close") and callable(resource.close):
                            close_method = resource.close

                            if asyncio.iscoroutinefunction(close_method):
                                await close_method()
                            else:
                                close_method()

                        elif hasattr(resource, "__aexit__") and callable(
                            resource.__aexit__
                        ):
                            aexit_method = resource.__aexit__
                            await aexit_method(None, None, None)

                        elif hasattr(resource, "__exit__") and callable(
                            resource.__exit__
                        ):
                            exit_method = resource.__exit__
                            exit_method(None, None, None)
                        else:
                            logger.warning(
                                f"No cleanup method found for resource: {cleanup.description}"
                            )

                    logger.debug(f"Cleaned up resource: {cleanup.description}")

                except Exception as e:
                    logger.error(
                        f"Error cleaning up resource {cleanup.description}: {e}"
                    )
                    logger.debug(traceback.format_exc())

                    # Schedule retry if allowed
                    if cleanup.retry_count < cleanup.max_retries:
                        await self._schedule_retry(cleanup)
                    else:
                        logger.error(
                            f"Failed to clean up resource {cleanup.description} after {cleanup.retry_count} retries"
                        )

        finally:
            # Remove from active cleanups
            if cleanup.resource_id and cleanup.resource_id in self._active_cleanups:
                self._active_cleanups.remove(cleanup.resource_id)

    async def _schedule_retry(self, cleanup: ScheduledCleanup) -> None:
        """Schedule a retry for a failed cleanup.

        Args:
            cleanup: Failed cleanup operation
        """
        # Increment retry count
        cleanup.retry_count += 1
        cleanup.is_retry = True

        # Schedule retry with delay
        retry_time = time.time() + self.retry_delay
        cleanup.due_time = retry_time

        # Add to queue
        await self.schedule_cleanup(
            resource=cleanup.resource,
            cleanup_func=cleanup.cleanup_func,
            delay=self.retry_delay,
            priority=cleanup.priority,
            description=cleanup.description,
            max_retries=cleanup.max_retries,
            resource_id=cleanup.resource_id,
            is_retry=True,
            retry_count=cleanup.retry_count,
        )

        logger.debug(
            f"Scheduled retry {cleanup.retry_count}/{cleanup.max_retries} for resource {cleanup.description} in {self.retry_delay}s"
        )

    async def schedule_cleanup(
        self,
        resource: Any,
        cleanup_func: Optional[CleanupFunc] = None,
        delay: float = 0.0,
        priority: CleanupPriority = CleanupPriority.NORMAL,
        description: str = "",
        max_retries: Optional[int] = None,
        resource_id: str = "",
        use_weak_ref: bool = False,
        is_retry: bool = False,
        retry_count: int = 0,
    ) -> None:
        """Schedule a resource for cleanup.

        Args:
            resource: Resource to clean up
            cleanup_func: Optional function to call for cleanup
            delay: Delay in seconds before cleaning up
            priority: Priority for this cleanup
            description: Description of the resource (for logging)
            max_retries: Maximum number of retries (None to use default)
            resource_id: Optional resource ID for cancellation
            use_weak_ref: Whether to use a weak reference to the resource
            is_retry: Whether this is a retry
            retry_count: Number of retries attempted
        """
        # Generate resource ID if not provided
        if not resource_id:
            resource_id = f"resource_{id(resource)}"

        # Generate description if not provided
        if not description:
            description = f"{resource.__class__.__name__}({resource_id})"

        # Calculate due time
        due_time = time.time() + delay

        # Create cleanup object
        cleanup = ScheduledCleanup(
            due_time=due_time,
            priority=priority,
            resource=resource,
            cleanup_func=cleanup_func,
            description=description,
            is_retry=is_retry,
            retry_count=retry_count,
            max_retries=max_retries
            if max_retries is not None
            else self.default_max_retries,
            resource_id=resource_id,
        )

        # Use weak reference if requested
        if use_weak_ref:
            self._resource_refs[resource_id] = weakref.ref(
                resource, lambda _: self._remove_resource_ref(resource_id)
            )

        # Add to queue
        async with self._lock:
            heapq.heappush(self._cleanup_queue, cleanup)

        logger.debug(
            f"Scheduled cleanup for resource {description} with delay {delay}s and priority {priority.name}"
        )

        # Start scheduler if not running
        if not self._running:
            self.start()

    def _remove_resource_ref(self, resource_id: str) -> None:
        """Remove a resource reference when it's garbage collected.

        Args:
            resource_id: ID of the resource to remove
        """
        if resource_id in self._resource_refs:
            del self._resource_refs[resource_id]
            logger.debug(f"Resource {resource_id} garbage collected, reference removed")

    async def cancel_cleanup(self, resource_id: str) -> bool:
        """Cancel a scheduled cleanup.

        Args:
            resource_id: ID of the resource to cancel cleanup for

        Returns:
            True if the cleanup was cancelled, False otherwise
        """
        cancelled = False

        async with self._lock:
            # Find and remove from queue
            new_queue = []
            for cleanup in self._cleanup_queue:
                if cleanup.resource_id != resource_id:
                    new_queue.append(cleanup)
                else:
                    cancelled = True

            if cancelled:
                # Rebuild queue
                self._cleanup_queue = []
                for cleanup in new_queue:
                    heapq.heappush(self._cleanup_queue, cleanup)

                logger.debug(f"Cancelled cleanup for resource {resource_id}")

                # Remove resource reference
                if resource_id in self._resource_refs:
                    del self._resource_refs[resource_id]

        return cancelled

    async def cancel_all_cleanups(self) -> int:
        """Cancel all scheduled cleanups.

        Returns:
            Number of cleanups cancelled
        """
        async with self._lock:
            count = len(self._cleanup_queue)
            self._cleanup_queue = []
            self._resource_refs = {}

            logger.debug(f"Cancelled {count} scheduled cleanups")

            return count

    async def shutdown(self) -> None:
        """Shut down the cleanup scheduler."""
        # Stop scheduler
        self.stop()

        # Cancel all cleanups
        await self.cancel_all_cleanups()

        logger.debug("Cleanup scheduler shut down")


class DelayedCleanupContext:
    """Context manager for delayed resource cleanup.

    This context manager acquires a resource and schedules its cleanup
    after a delay when the context is exited.
    """

    def __init__(
        self,
        resource: Any,
        scheduler: CleanupScheduler,
        cleanup_func: Optional[CleanupFunc] = None,
        delay: float = 0.0,
        priority: CleanupPriority = CleanupPriority.NORMAL,
        description: str = "",
        resource_id: str = "",
    ) -> None:
        """Initialize the delayed cleanup context.

        Args:
            resource: Resource to clean up
            scheduler: Cleanup scheduler to use
            cleanup_func: Optional function to call for cleanup
            delay: Delay in seconds before cleaning up
            priority: Priority for this cleanup
            description: Description of the resource (for logging)
            resource_id: Optional resource ID for cancellation
        """
        self.resource = resource
        self.scheduler = scheduler
        self.cleanup_func = cleanup_func
        self.delay = delay
        self.priority = priority
        self.description = description or f"{resource.__class__.__name__}"
        self.resource_id = resource_id or f"resource_{id(resource)}"

    async def __aenter__(self) -> Any:
        """Enter the context and return the resource."""
        logger.debug(f"Acquired resource: {self.description}")
        return self.resource

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context and schedule resource cleanup."""
        # Schedule cleanup
        await self.scheduler.schedule_cleanup(
            resource=self.resource,
            cleanup_func=self.cleanup_func,
            delay=self.delay,
            priority=self.priority,
            description=self.description,
            resource_id=self.resource_id,
        )


# Global cleanup scheduler instance
_cleanup_scheduler: Optional[CleanupScheduler] = None


def get_cleanup_scheduler() -> CleanupScheduler:
    """Get the global cleanup scheduler instance.

    Returns:
        CleanupScheduler instance
    """
    global _cleanup_scheduler

    if _cleanup_scheduler is None:
        _cleanup_scheduler = CleanupScheduler()
        _cleanup_scheduler.start()

    return _cleanup_scheduler


async def schedule_cleanup(
    resource: Any,
    cleanup_func: Optional[CleanupFunc] = None,
    delay: float = 0.0,
    priority: CleanupPriority = CleanupPriority.NORMAL,
    description: str = "",
    max_retries: Optional[int] = None,
    resource_id: str = "",
    use_weak_ref: bool = False,
) -> None:
    """Schedule a resource for cleanup.

    Args:
        resource: Resource to clean up
        cleanup_func: Optional function to call for cleanup
        delay: Delay in seconds before cleaning up
        priority: Priority for this cleanup
        description: Description of the resource (for logging)
        max_retries: Maximum number of retries (None to use default)
        resource_id: Optional resource ID for cancellation
        use_weak_ref: Whether to use a weak reference to the resource
    """
    scheduler = get_cleanup_scheduler()

    await scheduler.schedule_cleanup(
        resource=resource,
        cleanup_func=cleanup_func,
        delay=delay,
        priority=priority,
        description=description,
        max_retries=max_retries,
        resource_id=resource_id,
        use_weak_ref=use_weak_ref,
    )


async def cancel_cleanup(resource_id: str) -> bool:
    """Cancel a scheduled cleanup.

    Args:
        resource_id: ID of the resource to cancel cleanup for

    Returns:
        True if the cleanup was cancelled, False otherwise
    """
    scheduler = get_cleanup_scheduler()
    return await scheduler.cancel_cleanup(resource_id)


async def delayed_cleanup(
    resource: Any,
    delay: float,
    cleanup_func: Optional[CleanupFunc] = None,
    priority: CleanupPriority = CleanupPriority.NORMAL,
    description: str = "",
    resource_id: str = "",
) -> DelayedCleanupContext:
    """Create a context manager for delayed resource cleanup.

    Args:
        resource: Resource to clean up
        delay: Delay in seconds before cleaning up
        cleanup_func: Optional function to call for cleanup
        priority: Priority for this cleanup
        description: Description of the resource (for logging)
        resource_id: Optional resource ID for cancellation

    Returns:
        DelayedCleanupContext for use in an async with statement
    """
    scheduler = get_cleanup_scheduler()

    return DelayedCleanupContext(
        resource=resource,
        scheduler=scheduler,
        cleanup_func=cleanup_func,
        delay=delay,
        priority=priority,
        description=description,
        resource_id=resource_id,
    )


async def shutdown_cleanup_scheduler() -> None:
    """Shut down the global cleanup scheduler."""
    global _cleanup_scheduler

    if _cleanup_scheduler is not None:
        await _cleanup_scheduler.shutdown()
        _cleanup_scheduler = None
