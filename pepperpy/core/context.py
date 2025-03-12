"""Context managers for resource management.

This module provides context managers for resource management in the PepperPy
framework. Context managers ensure that resources are properly acquired and
released, even in the presence of exceptions.
"""

import asyncio
import contextlib
import time
from abc import abstractmethod
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union

from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic context managers
T = TypeVar("T")  # Resource type
R = TypeVar("R")  # Result type


class ResourceManager(Generic[T]):
    """Base class for resource managers.

    This class provides the foundation for implementing resource managers
    in the PepperPy framework. It defines the basic structure and common
    methods for resource acquisition and release.
    """

    def __init__(self, name: str):
        """Initialize the resource manager.

        Args:
            name: The name of the resource manager
        """
        self._name = name
        self._metadata: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Get the name of the resource manager.

        Returns:
            The name of the resource manager
        """
        return self._name

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata of the resource manager.

        Returns:
            The metadata of the resource manager
        """
        return self._metadata

    def with_metadata(self, key: str, value: Any) -> "ResourceManager[T]":
        """Add metadata to the resource manager.

        Args:
            key: The metadata key
            value: The metadata value

        Returns:
            Self for method chaining
        """
        self._metadata[key] = value
        return self

    @abstractmethod
    def acquire(self) -> T:
        """Acquire the resource.

        Returns:
            The acquired resource
        """
        pass

    @abstractmethod
    def release(self, resource: T) -> None:
        """Release the resource.

        Args:
            resource: The resource to release
        """
        pass

    def __enter__(self) -> T:
        """Enter the context manager.

        Returns:
            The acquired resource
        """
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised
        """
        if hasattr(self, "_resource") and self._resource is not None:
            self.release(self._resource)
            self._resource = None


class AsyncResourceManager(Generic[T]):
    """Base class for asynchronous resource managers.

    This class provides the foundation for implementing asynchronous resource
    managers in the PepperPy framework. It defines the basic structure and
    common methods for asynchronous resource acquisition and release.
    """

    def __init__(self, name: str):
        """Initialize the asynchronous resource manager.

        Args:
            name: The name of the resource manager
        """
        self._name = name
        self._metadata: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Get the name of the resource manager.

        Returns:
            The name of the resource manager
        """
        return self._name

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata of the resource manager.

        Returns:
            The metadata of the resource manager
        """
        return self._metadata

    def with_metadata(self, key: str, value: Any) -> "AsyncResourceManager[T]":
        """Add metadata to the resource manager.

        Args:
            key: The metadata key
            value: The metadata value

        Returns:
            Self for method chaining
        """
        self._metadata[key] = value
        return self

    @abstractmethod
    async def acquire(self) -> T:
        """Acquire the resource asynchronously.

        Returns:
            The acquired resource
        """
        pass

    @abstractmethod
    async def release(self, resource: T) -> None:
        """Release the resource asynchronously.

        Args:
            resource: The resource to release
        """
        pass

    async def __aenter__(self) -> T:
        """Enter the asynchronous context manager.

        Returns:
            The acquired resource
        """
        return await self.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the asynchronous context manager.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised
        """
        if hasattr(self, "_resource") and self._resource is not None:
            await self.release(self._resource)
            self._resource = None


class PooledResourceManager(ResourceManager[T]):
    """Resource manager for pooled resources.

    This class provides a resource manager for pooled resources, where
    resources are acquired from a pool and returned to the pool when
    they are no longer needed.
    """

    def __init__(
        self,
        name: str,
        factory: Callable[[], T],
        max_size: int = 10,
        min_size: int = 0,
        timeout: float = 5.0,
    ):
        """Initialize the pooled resource manager.

        Args:
            name: The name of the resource manager
            factory: A function that creates a new resource
            max_size: The maximum number of resources in the pool
            min_size: The minimum number of resources to keep in the pool
            timeout: The timeout for acquiring a resource, in seconds
        """
        super().__init__(name)
        self._factory = factory
        self._max_size = max_size
        self._min_size = min_size
        self._timeout = timeout
        self._pool: List[T] = []
        self._in_use: Dict[T, float] = {}
        self._lock = asyncio.Lock()

    def acquire(self) -> T:
        """Acquire a resource from the pool.

        Returns:
            The acquired resource

        Raises:
            PepperpyError: If a resource cannot be acquired within the timeout
        """
        start_time = time.time()
        while time.time() - start_time < self._timeout:
            # Try to get a resource from the pool
            if self._pool:
                resource = self._pool.pop()
                self._in_use[resource] = time.time()
                return resource

            # If the pool is empty but we haven't reached the max size,
            # create a new resource
            if len(self._in_use) < self._max_size:
                resource = self._factory()
                self._in_use[resource] = time.time()
                return resource

            # If we've reached the max size, wait and try again
            time.sleep(0.1)

        # If we've timed out, raise an error
        raise PepperpyError(
            f"Timed out waiting for a resource from pool '{self._name}'"
        )

    def release(self, resource: T) -> None:
        """Release a resource back to the pool.

        Args:
            resource: The resource to release

        Raises:
            PepperpyError: If the resource is not in use
        """
        if resource not in self._in_use:
            raise PepperpyError(
                f"Resource is not in use and cannot be released to pool '{self._name}'"
            )

        # Remove the resource from the in-use list
        del self._in_use[resource]

        # If we haven't reached the min size, add the resource back to the pool
        if len(self._pool) < self._min_size:
            self._pool.append(resource)
        else:
            # Otherwise, close the resource if it has a close method
            if hasattr(resource, "close") and callable(getattr(resource, "close")):
                resource.close()


class AsyncPooledResourceManager(AsyncResourceManager[T]):
    """Asynchronous resource manager for pooled resources.

    This class provides an asynchronous resource manager for pooled resources,
    where resources are acquired from a pool and returned to the pool when
    they are no longer needed.
    """

    def __init__(
        self,
        name: str,
        factory: Callable[[], T],
        max_size: int = 10,
        min_size: int = 0,
        timeout: float = 5.0,
    ):
        """Initialize the asynchronous pooled resource manager.

        Args:
            name: The name of the resource manager
            factory: A function that creates a new resource
            max_size: The maximum number of resources in the pool
            min_size: The minimum number of resources to keep in the pool
            timeout: The timeout for acquiring a resource, in seconds
        """
        super().__init__(name)
        self._factory = factory
        self._max_size = max_size
        self._min_size = min_size
        self._timeout = timeout
        self._pool: List[T] = []
        self._in_use: Dict[T, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(self) -> T:
        """Acquire a resource from the pool asynchronously.

        Returns:
            The acquired resource

        Raises:
            PepperpyError: If a resource cannot be acquired within the timeout
        """
        start_time = time.time()
        while time.time() - start_time < self._timeout:
            # Try to get a resource from the pool
            async with self._lock:
                if self._pool:
                    resource = self._pool.pop()
                    self._in_use[resource] = time.time()
                    return resource

                # If the pool is empty but we haven't reached the max size,
                # create a new resource
                if len(self._in_use) < self._max_size:
                    resource = self._factory()
                    self._in_use[resource] = time.time()
                    return resource

            # If we've reached the max size, wait and try again
            await asyncio.sleep(0.1)

        # If we've timed out, raise an error
        raise PepperpyError(
            f"Timed out waiting for a resource from pool '{self._name}'"
        )

    async def release(self, resource: T) -> None:
        """Release a resource back to the pool asynchronously.

        Args:
            resource: The resource to release

        Raises:
            PepperpyError: If the resource is not in use
        """
        async with self._lock:
            if resource not in self._in_use:
                raise PepperpyError(
                    f"Resource is not in use and cannot be released to pool '{self._name}'"
                )

            # Remove the resource from the in-use list
            del self._in_use[resource]

            # If we haven't reached the min size, add the resource back to the pool
            if len(self._pool) < self._min_size:
                self._pool.append(resource)
            else:
                # Otherwise, close the resource if it has a close method
                if hasattr(resource, "close") and callable(getattr(resource, "close")):
                    if asyncio.iscoroutinefunction(getattr(resource, "close")):
                        await resource.close()
                    else:
                        resource.close()


@contextlib.contextmanager
def resource_context(
    acquire_func: Callable[[], T], release_func: Callable[[T], None]
) -> T:
    """Create a context manager for a resource.

    Args:
        acquire_func: A function that acquires the resource
        release_func: A function that releases the resource

    Yields:
        The acquired resource
    """
    resource = acquire_func()
    try:
        yield resource
    finally:
        release_func(resource)


@contextlib.asynccontextmanager
async def async_resource_context(
    acquire_func: Callable[[], T], release_func: Callable[[T], None]
) -> T:
    """Create an asynchronous context manager for a resource.

    Args:
        acquire_func: A function that acquires the resource
        release_func: A function that releases the resource

    Yields:
        The acquired resource
    """
    resource = acquire_func()
    try:
        yield resource
    finally:
        if asyncio.iscoroutinefunction(release_func):
            await release_func(resource)
        else:
            release_func(resource)


class TimedContext:
    """Context manager for timing operations.

    This context manager measures the time taken to execute the code
    within the context and provides the elapsed time.
    """

    def __init__(self, name: str = "operation"):
        """Initialize the timed context.

        Args:
            name: The name of the operation being timed
        """
        self._name = name
        self._start_time = 0.0
        self._end_time = 0.0

    def __enter__(self) -> "TimedContext":
        """Enter the context manager.

        Returns:
            Self for accessing timing information
        """
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised
        """
        self._end_time = time.time()

    @property
    def elapsed(self) -> float:
        """Get the elapsed time.

        Returns:
            The elapsed time in seconds
        """
        if self._end_time == 0.0:
            return time.time() - self._start_time
        return self._end_time - self._start_time

    @property
    def name(self) -> str:
        """Get the name of the operation.

        Returns:
            The name of the operation
        """
        return self._name


class AsyncTimedContext:
    """Asynchronous context manager for timing operations.

    This context manager measures the time taken to execute the code
    within the context and provides the elapsed time.
    """

    def __init__(self, name: str = "operation"):
        """Initialize the asynchronous timed context.

        Args:
            name: The name of the operation being timed
        """
        self._name = name
        self._start_time = 0.0
        self._end_time = 0.0

    async def __aenter__(self) -> "AsyncTimedContext":
        """Enter the asynchronous context manager.

        Returns:
            Self for accessing timing information
        """
        self._start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the asynchronous context manager.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised
        """
        self._end_time = time.time()

    @property
    def elapsed(self) -> float:
        """Get the elapsed time.

        Returns:
            The elapsed time in seconds
        """
        if self._end_time == 0.0:
            return time.time() - self._start_time
        return self._end_time - self._start_time

    @property
    def name(self) -> str:
        """Get the name of the operation.

        Returns:
            The name of the operation
        """
        return self._name


class RetryContext:
    """Context manager for retrying operations.

    This context manager retries an operation if it fails, with
    configurable retry count, delay, and backoff.
    """

    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    ):
        """Initialize the retry context.

        Args:
            max_retries: The maximum number of retries
            delay: The initial delay between retries, in seconds
            backoff: The backoff factor for increasing the delay
            exceptions: The exception types to catch and retry
        """
        self._max_retries = max_retries
        self._delay = delay
        self._backoff = backoff
        self._exceptions = exceptions if isinstance(exceptions, list) else [exceptions]
        self._retry_count = 0
        self._last_exception = None

    def __enter__(self) -> "RetryContext":
        """Enter the context manager.

        Returns:
            Self for accessing retry information
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the context manager.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised

        Returns:
            True if the exception should be suppressed, False otherwise
        """
        if exc_type is None:
            return False

        # Check if the exception is one we should retry
        should_retry = False
        for exception_type in self._exceptions:
            if issubclass(exc_type, exception_type):
                should_retry = True
                break

        if not should_retry:
            return False

        # Check if we've reached the maximum number of retries
        if self._retry_count >= self._max_retries:
            return False

        # Increment the retry count and sleep
        self._retry_count += 1
        self._last_exception = exc_val
        time.sleep(self._delay * (self._backoff ** (self._retry_count - 1)))

        # Suppress the exception and retry
        return True

    @property
    def retry_count(self) -> int:
        """Get the current retry count.

        Returns:
            The current retry count
        """
        return self._retry_count

    @property
    def last_exception(self) -> Optional[Exception]:
        """Get the last exception that was caught.

        Returns:
            The last exception that was caught, or None if no exception was caught
        """
        return self._last_exception


class AsyncRetryContext:
    """Asynchronous context manager for retrying operations.

    This context manager retries an asynchronous operation if it fails,
    with configurable retry count, delay, and backoff.
    """

    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    ):
        """Initialize the asynchronous retry context.

        Args:
            max_retries: The maximum number of retries
            delay: The initial delay between retries, in seconds
            backoff: The backoff factor for increasing the delay
            exceptions: The exception types to catch and retry
        """
        self._max_retries = max_retries
        self._delay = delay
        self._backoff = backoff
        self._exceptions = exceptions if isinstance(exceptions, list) else [exceptions]
        self._retry_count = 0
        self._last_exception = None

    async def __aenter__(self) -> "AsyncRetryContext":
        """Enter the asynchronous context manager.

        Returns:
            Self for accessing retry information
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the asynchronous context manager.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised

        Returns:
            True if the exception should be suppressed, False otherwise
        """
        if exc_type is None:
            return False

        # Check if the exception is one we should retry
        should_retry = False
        for exception_type in self._exceptions:
            if issubclass(exc_type, exception_type):
                should_retry = True
                break

        if not should_retry:
            return False

        # Check if we've reached the maximum number of retries
        if self._retry_count >= self._max_retries:
            return False

        # Increment the retry count and sleep
        self._retry_count += 1
        self._last_exception = exc_val
        await asyncio.sleep(self._delay * (self._backoff ** (self._retry_count - 1)))

        # Suppress the exception and retry
        return True

    @property
    def retry_count(self) -> int:
        """Get the current retry count.

        Returns:
            The current retry count
        """
        return self._retry_count

    @property
    def last_exception(self) -> Optional[Exception]:
        """Get the last exception that was caught.

        Returns:
            The last exception that was caught, or None if no exception was caught
        """
        return self._last_exception


def timed(name: str = "operation") -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Decorator for timing functions.

    Args:
        name: The name of the operation being timed

    Returns:
        A decorator function
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        def wrapper(*args: Any, **kwargs: Any) -> R:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            with TimedContext(name) as timer:
                result = func(*args, **kwargs)
            logger.debug(f"{name} took {timer.elapsed:.3f} seconds")
            return result

        return wrapper

    return decorator


def async_timed(
    name: str = "operation",
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Decorator for timing asynchronous functions.

    Args:
        name: The name of the operation being timed

    Returns:
        A decorator function
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        async def wrapper(*args: Any, **kwargs: Any) -> R:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            async with AsyncTimedContext(name) as timer:
                result = await func(*args, **kwargs)
            logger.debug(f"{name} took {timer.elapsed:.3f} seconds")
            return result

        return wrapper

    return decorator


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Decorator for retrying functions.

    Args:
        max_retries: The maximum number of retries
        delay: The initial delay between retries, in seconds
        backoff: The backoff factor for increasing the delay
        exceptions: The exception types to catch and retry

    Returns:
        A decorator function
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        def wrapper(*args: Any, **kwargs: Any) -> R:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            retry_count = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check if the exception is one we should retry
                    should_retry = False
                    for exception_type in (
                        exceptions if isinstance(exceptions, list) else [exceptions]
                    ):
                        if isinstance(e, exception_type):
                            should_retry = True
                            break

                    if not should_retry:
                        raise

                    # Check if we've reached the maximum number of retries
                    if retry_count >= max_retries:
                        raise

                    # Increment the retry count and sleep
                    retry_count += 1
                    time.sleep(delay * (backoff ** (retry_count - 1)))

        return wrapper

    return decorator


def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Decorator for retrying asynchronous functions.

    Args:
        max_retries: The maximum number of retries
        delay: The initial delay between retries, in seconds
        backoff: The backoff factor for increasing the delay
        exceptions: The exception types to catch and retry

    Returns:
        A decorator function
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        async def wrapper(*args: Any, **kwargs: Any) -> R:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            retry_count = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Check if the exception is one we should retry
                    should_retry = False
                    for exception_type in (
                        exceptions if isinstance(exceptions, list) else [exceptions]
                    ):
                        if isinstance(e, exception_type):
                            should_retry = True
                            break

                    if not should_retry:
                        raise

                    # Check if we've reached the maximum number of retries
                    if retry_count >= max_retries:
                        raise

                    # Increment the retry count and sleep
                    retry_count += 1
                    await asyncio.sleep(delay * (backoff ** (retry_count - 1)))

        return wrapper

    return decorator
