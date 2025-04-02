"""Lazy initialization for PepperPy plugins.

This module provides utilities for lazy initialization of resources,
including on-demand initialization, prioritization, and background
initialization for expensive resources.
"""

import asyncio
import functools
import inspect
import time
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union, cast

from pepperpy.core.errors import ResourceError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type variables
T = TypeVar("T")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


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


class InitializationStatus:
    """Status of a lazily initialized resource."""

    def __init__(
        self,
        name: str,
        priority: InitializationPriority = InitializationPriority.NORMAL,
    ) -> None:
        """Initialize initialization status.

        Args:
            name: Name of the resource
            priority: Initialization priority
        """
        self.name = name
        self.priority = priority
        self.initialized = False
        self.initializing = False
        self.error: Optional[Exception] = None
        self.initialization_time: Optional[float] = None
        self.last_accessed: Optional[float] = None
        self.access_count = 0
        self.start_time: Optional[float] = None
        self.completion_time: Optional[float] = None
        self.initialization_time_ms: Optional[float] = None
        self._future: Optional[asyncio.Future] = None

    def mark_access(self) -> None:
        """Mark that the resource was accessed."""
        self.last_accessed = time.time()
        self.access_count += 1

    def start_initialization(self) -> None:
        """Mark that initialization has started."""
        self.initializing = True
        self.start_time = time.time()
        self._future = asyncio.Future()

    def complete_initialization(
        self, success: bool, error: Optional[Exception] = None
    ) -> None:
        """Mark that initialization has completed.

        Args:
            success: Whether initialization was successful
            error: Optional error that occurred during initialization
        """
        self.initializing = False
        self.initialized = success
        self.error = error
        self.completion_time = time.time()

        if self.start_time is not None and self.completion_time is not None:
            self.initialization_time_ms = (
                self.completion_time - self.start_time
            ) * 1000

        # Resolve the future
        if self._future is not None:
            if success:
                self._future.set_result(None)
            else:
                self._future.set_exception(
                    error or ResourceError(f"Failed to initialize {self.name}")
                )

    async def wait_for_initialization(self) -> None:
        """Wait for initialization to complete.

        Raises:
            ResourceError: If initialization failed
        """
        if self.initialized:
            return

        if not self.initializing or self._future is None:
            raise ResourceError(f"Resource {self.name} is not being initialized")

        await self._future

        if not self.initialized:
            raise ResourceError(
                f"Resource {self.name} failed to initialize: {self.error}"
            )


class ResourceInitializer:
    """Manager for lazily initialized resources."""

    def __init__(self, max_concurrent_initializations: int = 5) -> None:
        """Initialize the resource initializer.

        Args:
            max_concurrent_initializations: Maximum number of concurrent initializations
        """
        self._resources: Dict[str, Any] = {}
        self._status: Dict[str, InitializationStatus] = {}
        self._initializers: Dict[str, Callable[[], Any]] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        self._initialization_queue: List[str] = []
        self._initialization_semaphore = asyncio.Semaphore(
            max_concurrent_initializations
        )
        self._thread_pool = ThreadPoolExecutor()
        self._background_task: Optional[asyncio.Task] = None

    async def register_resource(
        self,
        name: str,
        initializer: Callable[[], Union[T, asyncio.Future[T]]],
        priority: InitializationPriority = InitializationPriority.NORMAL,
        dependencies: Optional[List[str]] = None,
    ) -> None:
        """Register a resource for lazy initialization.

        Args:
            name: Name of the resource
            initializer: Function to initialize the resource
            priority: Initialization priority
            dependencies: Optional list of dependencies

        Raises:
            ResourceError: If the resource is already registered
        """
        async with self._lock:
            if name in self._status:
                raise ResourceError(f"Resource {name} is already registered")

            # Create status
            status = InitializationStatus(name, priority)
            self._status[name] = status

            # Store initializer
            self._initializers[name] = initializer

            # Store dependencies
            if dependencies:
                self._dependencies[name] = set(dependencies)

                # Check for circular dependencies
                if self._has_circular_dependency(name, set()):
                    del self._status[name]
                    del self._initializers[name]
                    del self._dependencies[name]
                    raise ResourceError(
                        f"Circular dependency detected for resource {name}"
                    )
            else:
                self._dependencies[name] = set()

            # Add to initialization queue based on priority
            self._add_to_queue(name)

            logger.debug(
                f"Registered resource {name} for lazy initialization (priority: {priority.name})"
            )

            # Start background initialization if not already running
            self._ensure_background_task()

    def _has_circular_dependency(self, name: str, visited: Set[str]) -> bool:
        """Check if a resource has a circular dependency.

        Args:
            name: Name of the resource to check
            visited: Set of visited resources

        Returns:
            True if a circular dependency is detected, False otherwise
        """
        if name in visited:
            return True

        visited.add(name)

        for dependency in self._dependencies.get(name, set()):
            if dependency in self._dependencies and self._has_circular_dependency(
                dependency, visited.copy()
            ):
                return True

        return False

    def _add_to_queue(self, name: str) -> None:
        """Add a resource to the initialization queue.

        Args:
            name: Name of the resource to add
        """
        # Don't add if already in queue
        if name in self._initialization_queue:
            return

        # Add to queue based on priority
        priority = self._status[name].priority

        # Find the insertion point based on priority
        for i, queued_name in enumerate(self._initialization_queue):
            if self._status[queued_name].priority < priority:
                self._initialization_queue.insert(i, name)
                return

        # If we get here, add to the end
        self._initialization_queue.append(name)

    def _ensure_background_task(self) -> None:
        """Ensure the background initialization task is running."""
        if self._background_task is None or self._background_task.done():
            self._background_task = asyncio.create_task(
                self._background_initialization()
            )

    async def _background_initialization(self) -> None:
        """Background task to initialize resources."""
        try:
            while True:
                # Get the next resource to initialize
                resource_name = None

                async with self._lock:
                    # Check if there are any resources to initialize
                    if not self._initialization_queue:
                        # Nothing to initialize, exit
                        return

                    # Get the next resource
                    for name in list(self._initialization_queue):
                        status = self._status[name]

                        # Skip if already initialized or initializing
                        if status.initialized or status.initializing:
                            self._initialization_queue.remove(name)
                            continue

                        # Check if all dependencies are initialized
                        dependencies = self._dependencies.get(name, set())
                        all_deps_initialized = all(
                            dep not in self._status or self._status[dep].initialized
                            for dep in dependencies
                        )

                        if all_deps_initialized:
                            resource_name = name
                            self._initialization_queue.remove(name)
                            break

                # If we found a resource to initialize, do it
                if resource_name:
                    # Acquire the semaphore
                    async with self._initialization_semaphore:
                        await self._initialize_resource(resource_name)
                else:
                    # Wait for dependencies to be initialized
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            logger.debug("Background initialization task cancelled")
        except Exception as e:
            logger.error(f"Error in background initialization task: {e}")

    async def _initialize_resource(self, name: str) -> None:
        """Initialize a resource.

        Args:
            name: Name of the resource to initialize
        """
        status = self._status[name]

        # Mark as initializing
        status.start_initialization()
        logger.debug(f"Starting initialization of resource {name}")

        try:
            # Initialize dependencies first
            for dependency in self._dependencies.get(name, set()):
                if (
                    dependency in self._status
                    and not self._status[dependency].initialized
                ):
                    await self.get_resource(dependency)

            # Call the initializer
            initializer = self._initializers[name]

            if asyncio.iscoroutinefunction(initializer):
                # Async initializer
                result = await initializer()
            elif inspect.isgeneratorfunction(initializer):
                # Generator function (should be avoided)
                logger.warning(
                    f"Generator function used as initializer for {name}, this may cause issues"
                )
                result = initializer()
            else:
                # Sync initializer, run in thread pool
                result = await asyncio.get_event_loop().run_in_executor(
                    self._thread_pool, initializer
                )

            # Handle future return type
            if isinstance(result, asyncio.Future):
                result = await result

            # Store the result
            self._resources[name] = result

            # Mark as initialized
            status.complete_initialization(True)
            logger.debug(f"Initialized resource {name} successfully")

        except Exception as e:
            # Mark as failed
            status.complete_initialization(False, e)
            logger.error(f"Failed to initialize resource {name}: {e}")

            # Re-add to queue for retry
            async with self._lock:
                self._add_to_queue(name)

    async def get_resource(self, name: str, blocking: bool = True) -> Any:
        """Get a resource, initializing it if necessary.

        Args:
            name: Name of the resource to get
            blocking: Whether to block until initialization completes

        Returns:
            The initialized resource

        Raises:
            ResourceError: If the resource is not registered or initialization failed
        """
        # Check if resource exists
        if name not in self._status:
            raise ResourceError(f"Resource {name} is not registered")

        status = self._status[name]

        # Mark access
        status.mark_access()

        # Check if already initialized
        if status.initialized:
            return self._resources[name]

        # Check if initializing
        if status.initializing:
            if blocking:
                await status.wait_for_initialization()
                return self._resources[name]
            else:
                raise ResourceError(f"Resource {name} is still initializing")

        # Initialize now
        async with self._lock:
            # Check again in case it was initialized while acquiring the lock
            if status.initialized:
                return self._resources[name]

            if status.initializing:
                if blocking:
                    await status.wait_for_initialization()
                    return self._resources[name]
                else:
                    raise ResourceError(f"Resource {name} is still initializing")

            # Start initialization
            await self._initialize_resource(name)

            if blocking:
                return self._resources[name]
            else:
                raise ResourceError(f"Resource {name} is now initializing")

    def is_initialized(self, name: str) -> bool:
        """Check if a resource is initialized.

        Args:
            name: Name of the resource to check

        Returns:
            True if the resource is initialized, False otherwise
        """
        return name in self._status and self._status[name].initialized

    def get_initialization_status(self, name: str) -> Optional[InitializationStatus]:
        """Get the initialization status of a resource.

        Args:
            name: Name of the resource to check

        Returns:
            InitializationStatus if the resource is registered, None otherwise
        """
        return self._status.get(name)

    def get_all_statuses(self) -> Dict[str, InitializationStatus]:
        """Get the initialization status of all resources.

        Returns:
            Dictionary mapping resource names to their initialization status
        """
        return dict(self._status)

    async def initialize_all(self, blocking: bool = True) -> None:
        """Initialize all registered resources.

        Args:
            blocking: Whether to block until all initializations complete
        """
        async with self._lock:
            # Create a copy of the resources to initialize
            resources = list(self._status.keys())

        # Initialize each resource
        for name in resources:
            if blocking:
                await self.get_resource(name, blocking=True)
            else:
                try:
                    await self.get_resource(name, blocking=False)
                except ResourceError:
                    # Resource is initializing, continue
                    pass

    async def initialize_priority(
        self, priority: InitializationPriority, blocking: bool = True
    ) -> None:
        """Initialize all resources with at least the given priority.

        Args:
            priority: Minimum priority to initialize
            blocking: Whether to block until all initializations complete
        """
        async with self._lock:
            # Create a copy of the resources to initialize
            resources = [
                name
                for name, status in self._status.items()
                if status.priority >= priority
            ]

        # Initialize each resource
        for name in resources:
            if blocking:
                await self.get_resource(name, blocking=True)
            else:
                try:
                    await self.get_resource(name, blocking=False)
                except ResourceError:
                    # Resource is initializing, continue
                    pass

    async def shutdown(self) -> None:
        """Shutdown the resource initializer."""
        # Cancel background task
        if self._background_task is not None:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

        # Shutdown thread pool
        self._thread_pool.shutdown()

        logger.debug("Resource initializer shut down")


# Global resource initializer instance
_resource_initializer: Optional[ResourceInitializer] = None


def get_resource_initializer() -> ResourceInitializer:
    """Get the global resource initializer.

    Returns:
        ResourceInitializer instance
    """
    global _resource_initializer
    if _resource_initializer is None:
        _resource_initializer = ResourceInitializer()

    return _resource_initializer


def lazy_property(
    func: Optional[Callable[[Any], T]] = None,
    *,
    priority: InitializationPriority = InitializationPriority.NORMAL,
    dependencies: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> Any:
    """Decorator for lazily initialized properties.

    Args:
        func: Property function
        priority: Initialization priority
        dependencies: Optional list of dependencies
        name: Optional custom name for the resource

    Returns:
        Property object
    """

    def decorator(func: Callable[[Any], T]) -> property:
        prop_name = name or f"{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(self: Any) -> T:
            # Check if initialized
            if hasattr(self, f"_lazy_{func.__name__}"):
                return getattr(self, f"_lazy_{func.__name__}")

            # Initialize
            initializer = ResourceInitializer()

            # Define sync/async initializer functions
            if asyncio.iscoroutinefunction(func):

                async def async_init() -> T:
                    result = await func(self)
                    setattr(self, f"_lazy_{func.__name__}", result)
                    return result

                # Register and start initialization
                loop = asyncio.get_event_loop()
                loop.create_task(
                    initializer.register_resource(
                        name=prop_name,
                        initializer=async_init,
                        priority=priority,
                        dependencies=dependencies,
                    )
                )

                # This will actually be a blocking call (not ideal),
                # but we can't easily make properties async in Python
                result = loop.run_until_complete(initializer.get_resource(prop_name))
                return result

            else:
                # For sync properties
                def sync_init() -> T:
                    result = func(self)
                    setattr(self, f"_lazy_{func.__name__}", result)
                    return result

                # We can't easily register this with the initializer
                # in a sync context, so just do the initialization now
                result = sync_init()
                return result

        return property(wrapper)

    if func is None:
        return decorator
    return decorator(func)


async def lazy_init(
    name: str,
    initializer: Callable[[], T],
    priority: InitializationPriority = InitializationPriority.NORMAL,
    dependencies: Optional[List[str]] = None,
    blocking: bool = False,
) -> Optional[T]:
    """Initialize a resource lazily.

    Args:
        name: Name of the resource
        initializer: Function to initialize the resource
        priority: Initialization priority
        dependencies: Optional list of dependencies
        blocking: Whether to block until initialization completes

    Returns:
        The resource if blocking is True and initialization completes,
        None otherwise
    """
    initializer_instance = get_resource_initializer()

    # Register the resource
    await initializer_instance.register_resource(
        name=name, initializer=initializer, priority=priority, dependencies=dependencies
    )

    # Get the resource if blocking
    if blocking:
        return await initializer_instance.get_resource(name, blocking=True)
    else:
        try:
            return await initializer_instance.get_resource(name, blocking=False)
        except ResourceError:
            # Resource is initializing, return None
            return None


def prioritized(
    priority: InitializationPriority = InitializationPriority.NORMAL,
    dependencies: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator for prioritized initialization of methods.

    Args:
        priority: Initialization priority
        dependencies: Optional list of dependencies
        name: Optional custom name for the resource

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        # Generate a unique name for this function
        resource_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Get the initializer
            initializer = get_resource_initializer()

            # Define the initializer function
            async def init() -> Any:
                return await func(self, *args, **kwargs)

            # Register the resource
            await initializer.register_resource(
                name=resource_name,
                initializer=init,
                priority=priority,
                dependencies=dependencies,
            )

            # Get the resource
            return await initializer.get_resource(resource_name, blocking=True)

        @functools.wraps(func)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # For sync functions, we can't easily use the initializer
            # without blocking, so just call the function directly
            return func(self, *args, **kwargs)

        # Use the appropriate wrapper based on the function type
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


class background:
    """Decorator for background initialization of methods.

    This decorator schedules a method to be called in the background
    when the application is idle.
    """

    def __init__(
        self,
        priority: InitializationPriority = InitializationPriority.BACKGROUND,
        dependencies: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the decorator.

        Args:
            priority: Initialization priority
            dependencies: Optional list of dependencies
            name: Optional custom name for the resource
        """
        self.priority = priority
        self.dependencies = dependencies
        self.name = name

    def __call__(self, func: F) -> F:
        # Generate a unique name for this function
        resource_name = self.name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        async def async_wrapper(self_: Any, *args: Any, **kwargs: Any) -> Any:
            # This wrapper is just for registering the background task,
            # the actual initialization happens in the background
            initializer = get_resource_initializer()

            # Define the initializer function
            async def init() -> Any:
                return await func(self_, *args, **kwargs)

            # Register the resource
            await initializer.register_resource(
                name=resource_name,
                initializer=init,
                priority=self.priority,
                dependencies=self.dependencies,
            )

            # Just return None, initialization happens in the background
            return None

        @functools.wraps(func)
        def sync_wrapper(self_: Any, *args: Any, **kwargs: Any) -> None:
            # For sync functions, we can't easily use the initializer
            # without blocking, so create a task to register it
            async def register() -> None:
                initializer = get_resource_initializer()

                # Define the initializer function
                def init() -> Any:
                    return func(self_, *args, **kwargs)

                # Register the resource
                await initializer.register_resource(
                    name=resource_name,
                    initializer=init,
                    priority=self.priority,
                    dependencies=self.dependencies,
                )

            # Create a task to register the resource
            loop = asyncio.get_event_loop()
            loop.create_task(register())

            # Just return None, initialization happens in the background

        # Use the appropriate wrapper based on the function type
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)
