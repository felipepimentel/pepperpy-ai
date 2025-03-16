"""Resource tracking and management with automatic cleanup.

This module provides a centralized system for tracking and managing resources
across the application, with automatic cleanup capabilities to prevent resource
leaks and optimize memory usage.
"""

import asyncio
import atexit
import threading
import time
from abc import abstractmethod
from enum import Enum, auto
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from pepperpy.core.context import AsyncResourceManager, ResourceManager
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic resource tracking
T = TypeVar("T")  # Resource type


class ResourceState(Enum):
    """Enum representing the state of a resource."""

    CREATED = auto()
    ACTIVE = auto()
    IDLE = auto()
    CLOSING = auto()
    CLOSED = auto()
    ERROR = auto()


class ResourceType(Enum):
    """Enum representing the type of resource."""

    CONNECTION = auto()
    FILE = auto()
    MEMORY = auto()
    THREAD = auto()
    PROCESS = auto()
    LOCK = auto()
    CUSTOM = auto()


class ResourceInfo(Generic[T]):
    """Information about a tracked resource."""

    def __init__(
        self,
        resource: T,
        resource_type: ResourceType,
        cleanup_func: Union[Callable[[T], None], Callable[[T], Awaitable[None]]],
        idle_timeout: Optional[float] = None,
        max_age: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize resource information.

        Args:
            resource: The resource to track
            resource_type: The type of resource
            cleanup_func: Function to call to clean up the resource (sync or async)
            idle_timeout: Timeout in seconds after which an idle resource should be cleaned up
            max_age: Maximum age in seconds after which a resource should be cleaned up
            metadata: Additional metadata about the resource
        """
        self.resource = resource
        self.resource_id = id(resource)
        self.resource_type = resource_type
        self.cleanup_func = cleanup_func
        self.idle_timeout = idle_timeout
        self.max_age = max_age
        self.metadata = metadata or {}
        self.state = ResourceState.CREATED
        self.created_at = time.time()
        self.last_used_at = self.created_at
        self.error_count = 0
        self.is_async = asyncio.iscoroutinefunction(cleanup_func)

    def mark_active(self) -> None:
        """Mark the resource as active."""
        self.state = ResourceState.ACTIVE
        self.last_used_at = time.time()

    def mark_idle(self) -> None:
        """Mark the resource as idle."""
        self.state = ResourceState.IDLE
        self.last_used_at = time.time()

    def mark_closing(self) -> None:
        """Mark the resource as closing."""
        self.state = ResourceState.CLOSING

    def mark_closed(self) -> None:
        """Mark the resource as closed."""
        self.state = ResourceState.CLOSED

    def mark_error(self) -> None:
        """Mark the resource as having an error."""
        self.state = ResourceState.ERROR
        self.error_count += 1

    def should_cleanup(self, current_time: float) -> bool:
        """Check if the resource should be cleaned up.

        Args:
            current_time: The current time

        Returns:
            True if the resource should be cleaned up, False otherwise
        """
        # Don't clean up resources that are already closing or closed
        if self.state in (ResourceState.CLOSING, ResourceState.CLOSED):
            return False

        # Clean up resources with errors
        if self.state == ResourceState.ERROR and self.error_count > 3:
            return True

        # Clean up resources that have exceeded their maximum age
        if self.max_age is not None and current_time - self.created_at > self.max_age:
            return True

        # Clean up idle resources that have exceeded their idle timeout
        if (
            self.state == ResourceState.IDLE
            and self.idle_timeout is not None
            and current_time - self.last_used_at > self.idle_timeout
        ):
            return True

        return False

    def __str__(self) -> str:
        """Get a string representation of the resource information.

        Returns:
            A string representation of the resource information
        """
        return (
            f"ResourceInfo(id={self.resource_id}, type={self.resource_type.name}, "
            f"state={self.state.name}, age={time.time() - self.created_at:.2f}s, "
            f"idle={time.time() - self.last_used_at:.2f}s)"
        )


class ResourceTracker:
    """Centralized system for tracking and managing resources.

    This class provides a centralized system for tracking and managing resources
    across the application, with automatic cleanup capabilities to prevent resource
    leaks and optimize memory usage.
    """

    _instance = None
    _lock = threading.RLock()
    _initialized: bool = False

    def __new__(cls):
        """Create a new ResourceTracker instance.

        Returns:
            The singleton ResourceTracker instance
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ResourceTracker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the resource tracker."""
        with self._lock:
            if self._initialized:
                return
            self._initialized = True

            self._resources: Dict[int, ResourceInfo] = {}
            self._resource_types: Dict[ResourceType, Set[int]] = {
                resource_type: set() for resource_type in ResourceType
            }
            self._cleanup_thread = None
            self._cleanup_event = threading.Event()
            self._cleanup_interval = 60.0  # seconds
            self._async_loop = None
            self._stats = {
                "tracked": 0,
                "cleaned_up": 0,
                "errors": 0,
            }

            # Register cleanup on exit
            atexit.register(self.cleanup_all)

    def start_cleanup_thread(self) -> None:
        """Start the cleanup thread if it's not already running."""
        with self._lock:
            if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
                self._cleanup_event.clear()
                self._cleanup_thread = threading.Thread(
                    target=self._cleanup_loop,
                    name="ResourceTrackerCleanup",
                    daemon=True,
                )
                self._cleanup_thread.start()
                logger.info("Started resource tracker cleanup thread")

    def stop_cleanup_thread(self) -> None:
        """Stop the cleanup thread if it's running."""
        with self._lock:
            if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
                self._cleanup_event.set()
                self._cleanup_thread.join(timeout=5.0)
                if self._cleanup_thread.is_alive():
                    logger.warning(
                        "Resource tracker cleanup thread did not stop gracefully"
                    )
                else:
                    logger.info("Stopped resource tracker cleanup thread")
                self._cleanup_thread = None

    def set_cleanup_interval(self, interval: float) -> None:
        """Set the cleanup interval.

        Args:
            interval: The cleanup interval in seconds
        """
        with self._lock:
            self._cleanup_interval = max(1.0, interval)
            logger.info(
                f"Set resource tracker cleanup interval to {self._cleanup_interval}s"
            )

    def set_async_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the async event loop for cleaning up async resources.

        Args:
            loop: The async event loop
        """
        with self._lock:
            self._async_loop = loop
            logger.info("Set resource tracker async loop")

    def track(
        self,
        resource: T,
        resource_type: ResourceType,
        cleanup_func: Union[Callable[[T], None], Callable[[T], Awaitable[None]]],
        idle_timeout: Optional[float] = None,
        max_age: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> T:
        """Track a resource.

        Args:
            resource: The resource to track
            resource_type: The type of resource
            cleanup_func: Function to call to clean up the resource (sync or async)
            idle_timeout: Timeout in seconds after which an idle resource should be cleaned up
            max_age: Maximum age in seconds after which a resource should be cleaned up
            metadata: Additional metadata about the resource

        Returns:
            The tracked resource
        """
        with self._lock:
            resource_id = id(resource)
            if resource_id in self._resources:
                logger.warning(f"Resource {resource_id} is already being tracked")
                return resource

            resource_info = ResourceInfo(
                resource=resource,
                resource_type=resource_type,
                cleanup_func=cleanup_func,
                idle_timeout=idle_timeout,
                max_age=max_age,
                metadata=metadata,
            )
            self._resources[resource_id] = resource_info
            self._resource_types[resource_type].add(resource_id)
            self._stats["tracked"] += 1

            # Start the cleanup thread if it's not already running
            self.start_cleanup_thread()

            logger.debug(f"Tracking resource: {resource_info}")
            return resource

    def untrack(self, resource: T) -> None:
        """Stop tracking a resource without cleaning it up.

        Args:
            resource: The resource to stop tracking
        """
        with self._lock:
            resource_id = id(resource)
            if resource_id not in self._resources:
                logger.warning(f"Resource {resource_id} is not being tracked")
                return

            resource_info = self._resources[resource_id]
            del self._resources[resource_id]
            self._resource_types[resource_info.resource_type].remove(resource_id)
            logger.debug(f"Stopped tracking resource: {resource_info}")

    def mark_active(self, resource: T) -> None:
        """Mark a resource as active.

        Args:
            resource: The resource to mark as active
        """
        with self._lock:
            resource_id = id(resource)
            if resource_id not in self._resources:
                logger.warning(f"Resource {resource_id} is not being tracked")
                return

            self._resources[resource_id].mark_active()

    def mark_idle(self, resource: T) -> None:
        """Mark a resource as idle.

        Args:
            resource: The resource to mark as idle
        """
        with self._lock:
            resource_id = id(resource)
            if resource_id not in self._resources:
                logger.warning(f"Resource {resource_id} is not being tracked")
                return

            self._resources[resource_id].mark_idle()

    def cleanup(self, resource: T) -> bool:
        """Clean up a resource and stop tracking it.

        Args:
            resource: The resource to clean up

        Returns:
            True if the resource was cleaned up, False otherwise
        """
        with self._lock:
            resource_id = id(resource)
            if resource_id not in self._resources:
                logger.warning(f"Resource {resource_id} is not being tracked")
                return False

            resource_info = self._resources[resource_id]
            resource_info.mark_closing()

            try:
                if resource_info.is_async:
                    if self._async_loop is None:
                        logger.error(
                            f"Cannot clean up async resource {resource_id} without an async loop"
                        )
                        resource_info.mark_error()
                        return False

                    # Fix: Ensure we're passing a coroutine to run_coroutine_threadsafe
                    coro = resource_info.cleanup_func(resource_info.resource)
                    if coro is not None:  # Ensure the coroutine is not None
                        future = asyncio.run_coroutine_threadsafe(
                            coro,
                            self._async_loop,
                        )
                        future.result(timeout=5.0)
                else:
                    resource_info.cleanup_func(resource_info.resource)

                resource_info.mark_closed()
                self._stats["cleaned_up"] += 1
                logger.debug(f"Cleaned up resource: {resource_info}")
                self.untrack(resource)
                return True
            except Exception as e:
                resource_info.mark_error()
                self._stats["errors"] += 1
                logger.error(f"Error cleaning up resource {resource_id}: {e}")
                return False

    def cleanup_by_type(self, resource_type: ResourceType) -> Tuple[int, int]:
        """Clean up all resources of a specific type.

        Args:
            resource_type: The type of resources to clean up

        Returns:
            A tuple of (number of resources cleaned up, number of errors)
        """
        with self._lock:
            resource_ids = list(self._resource_types[resource_type])
            cleaned_up = 0
            errors = 0

            for resource_id in resource_ids:
                if resource_id in self._resources:
                    resource_info = self._resources[resource_id]
                    try:
                        if self.cleanup(resource_info.resource):
                            cleaned_up += 1
                        else:
                            errors += 1
                    except Exception as e:
                        errors += 1
                        logger.error(f"Error cleaning up resource {resource_id}: {e}")

            return cleaned_up, errors

    def cleanup_idle(self, max_idle_time: Optional[float] = None) -> Tuple[int, int]:
        """Clean up idle resources.

        Args:
            max_idle_time: Maximum idle time in seconds, or None to use each resource's idle_timeout

        Returns:
            A tuple of (number of resources cleaned up, number of errors)
        """
        with self._lock:
            current_time = time.time()
            cleaned_up = 0
            errors = 0

            for resource_id, resource_info in list(self._resources.items()):
                if resource_info.state != ResourceState.IDLE:
                    continue

                idle_time = current_time - resource_info.last_used_at
                should_cleanup = False

                if max_idle_time is not None and idle_time > max_idle_time:
                    should_cleanup = True
                elif (
                    resource_info.idle_timeout is not None
                    and idle_time > resource_info.idle_timeout
                ):
                    should_cleanup = True

                if should_cleanup:
                    try:
                        if self.cleanup(resource_info.resource):
                            cleaned_up += 1
                        else:
                            errors += 1
                    except Exception as e:
                        errors += 1
                        logger.error(
                            f"Error cleaning up idle resource {resource_id}: {e}"
                        )

            return cleaned_up, errors

    def cleanup_all(self) -> Tuple[int, int]:
        """Clean up all tracked resources.

        Returns:
            A tuple of (number of resources cleaned up, number of errors)
        """
        with self._lock:
            # Stop the cleanup thread first
            self.stop_cleanup_thread()

            cleaned_up = 0
            errors = 0

            for resource_id, resource_info in list(self._resources.items()):
                try:
                    if self.cleanup(resource_info.resource):
                        cleaned_up += 1
                    else:
                        errors += 1
                except Exception as e:
                    errors += 1
                    logger.error(f"Error cleaning up resource {resource_id}: {e}")

            return cleaned_up, errors

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked resources.

        Returns:
            A dictionary of statistics
        """
        with self._lock:
            # Create a copy of the stats dictionary
            stats: Dict[str, Any] = dict(self._stats)
            stats["current"] = len(self._resources)

            # Add type-specific stats
            type_stats: Dict[str, int] = {}
            for resource_type, resource_ids in self._resource_types.items():
                type_stats[resource_type.name] = len(resource_ids)
            stats["by_type"] = type_stats

            # Add state-specific stats
            state_stats: Dict[str, int] = {}
            for state in ResourceState:
                state_stats[state.name] = sum(
                    1 for info in self._resources.values() if info.state == state
                )
            stats["by_state"] = state_stats

            return stats

    def _cleanup_loop(self) -> None:
        """Background thread for periodic cleanup of resources."""
        logger.info("Resource tracker cleanup thread started")
        while not self._cleanup_event.is_set():
            try:
                # Sleep for a short interval and check the event frequently
                for _ in range(int(self._cleanup_interval * 10)):
                    if self._cleanup_event.is_set():
                        break
                    time.sleep(0.1)

                if self._cleanup_event.is_set():
                    break

                # Check for resources that need cleanup
                with self._lock:
                    current_time = time.time()
                    for resource_id, resource_info in list(self._resources.items()):
                        if resource_info.should_cleanup(current_time):
                            try:
                                self.cleanup(resource_info.resource)
                            except Exception as e:
                                logger.error(
                                    f"Error in cleanup loop for resource {resource_id}: {e}"
                                )
            except Exception as e:
                logger.error(f"Error in resource tracker cleanup loop: {e}")

        logger.info("Resource tracker cleanup thread stopped")


class TrackedResourceManager(ResourceManager[T]):
    """Resource manager that automatically tracks resources.

    This class extends ResourceManager to automatically track resources
    using the ResourceTracker.
    """

    def __init__(
        self,
        name: str,
        resource_type: ResourceType,
        idle_timeout: Optional[float] = None,
        max_age: Optional[float] = None,
    ):
        """Initialize the tracked resource manager.

        Args:
            name: The name of the resource manager
            resource_type: The type of resource
            idle_timeout: Timeout in seconds after which an idle resource should be cleaned up
            max_age: Maximum age in seconds after which a resource should be cleaned up
        """
        super().__init__(name)
        self._resource_type = resource_type
        self._idle_timeout = idle_timeout
        self._max_age = max_age
        self._tracker = ResourceTracker()

    @abstractmethod
    def create_resource(self) -> T:
        """Create a new resource.

        Returns:
            The created resource
        """
        pass

    @abstractmethod
    def cleanup_resource(self, resource: T) -> None:
        """Clean up a resource.

        Args:
            resource: The resource to clean up
        """
        pass

    def acquire(self) -> T:
        """Acquire a resource.

        Returns:
            The acquired resource
        """
        resource = self.create_resource()
        self._resource = self._tracker.track(
            resource=resource,
            resource_type=self._resource_type,
            cleanup_func=self.cleanup_resource,
            idle_timeout=self._idle_timeout,
            max_age=self._max_age,
            metadata={"manager": self.name, **self.metadata},
        )
        self._tracker.mark_active(self._resource)
        return self._resource

    def release(self, resource: T) -> None:
        """Release a resource.

        Args:
            resource: The resource to release
        """
        self._tracker.mark_idle(resource)


class AsyncTrackedResourceManager(AsyncResourceManager[T]):
    """Asynchronous resource manager that automatically tracks resources.

    This class extends AsyncResourceManager to automatically track resources
    using the ResourceTracker.
    """

    def __init__(
        self,
        name: str,
        resource_type: ResourceType,
        idle_timeout: Optional[float] = None,
        max_age: Optional[float] = None,
    ):
        """Initialize the asynchronous tracked resource manager.

        Args:
            name: The name of the resource manager
            resource_type: The type of resource
            idle_timeout: Timeout in seconds after which an idle resource should be cleaned up
            max_age: Maximum age in seconds after which a resource should be cleaned up
        """
        super().__init__(name)
        self._resource_type = resource_type
        self._idle_timeout = idle_timeout
        self._max_age = max_age
        self._tracker = ResourceTracker()

        # Set the async loop for the tracker
        loop = asyncio.get_event_loop()
        self._tracker.set_async_loop(loop)

    @abstractmethod
    async def create_resource(self) -> T:
        """Create a new resource asynchronously.

        Returns:
            The created resource
        """
        pass

    @abstractmethod
    async def cleanup_resource(self, resource: T) -> None:
        """Clean up a resource asynchronously.

        Args:
            resource: The resource to clean up
        """
        pass

    async def acquire(self) -> T:
        """Acquire a resource asynchronously.

        Returns:
            The acquired resource
        """
        resource = await self.create_resource()

        # Create a non-async wrapper that will call our async cleanup function
        def cleanup_wrapper(res: T) -> Any:
            # This function returns the coroutine that the ResourceTracker will run
            # in the appropriate async context
            return self.cleanup_resource(res)

        # Use the wrapper for tracking
        self._resource = self._tracker.track(
            resource=resource,
            resource_type=self._resource_type,
            cleanup_func=cast(Callable[[T], Any], cleanup_wrapper),
            idle_timeout=self._idle_timeout,
            max_age=self._max_age,
            metadata={"manager": self.name, **self.metadata},
        )
        self._tracker.mark_active(self._resource)
        return self._resource

    async def release(self, resource: T) -> None:
        """Release a resource asynchronously.

        Args:
            resource: The resource to release
        """
        self._tracker.mark_idle(resource)


# Convenience functions


def get_resource_tracker() -> ResourceTracker:
    """Get the singleton ResourceTracker instance.

    Returns:
        The ResourceTracker instance
    """
    return ResourceTracker()


def track_resource(
    resource: T,
    resource_type: ResourceType,
    cleanup_func: Union[Callable[[T], None], Callable[[T], Awaitable[None]]],
    idle_timeout: Optional[float] = None,
    max_age: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> T:
    """Track a resource.

    Args:
        resource: The resource to track
        resource_type: The type of resource
        cleanup_func: Function to call to clean up the resource (sync or async)
        idle_timeout: Timeout in seconds after which an idle resource should be cleaned up
        max_age: Maximum age in seconds after which a resource should be cleaned up
        metadata: Additional metadata about the resource

    Returns:
        The tracked resource
    """
    tracker = get_resource_tracker()
    return tracker.track(
        resource=resource,
        resource_type=resource_type,
        cleanup_func=cleanup_func,
        idle_timeout=idle_timeout,
        max_age=max_age,
        metadata=metadata,
    )


def cleanup_resource(resource: T) -> bool:
    """Clean up a resource and stop tracking it.

    Args:
        resource: The resource to clean up

    Returns:
        True if the resource was cleaned up, False otherwise
    """
    tracker = get_resource_tracker()
    return tracker.cleanup(resource)


def cleanup_all_resources() -> Tuple[int, int]:
    """Clean up all tracked resources.

    Returns:
        A tuple of (number of resources cleaned up, number of errors)
    """
    tracker = get_resource_tracker()
    return tracker.cleanup_all()


def get_resource_stats() -> Dict[str, Any]:
    """Get statistics about tracked resources.

    Returns:
        A dictionary of statistics
    """
    tracker = get_resource_tracker()
    return tracker.get_stats()
