"""Decorators for common patterns in PepperPy.

This module provides decorator utilities for the PepperPy framework, including:
- Retry mechanisms with exponential backoff
- Timing utilities
- Deprecation warnings
- Memoization patterns
- Logging enhancers
"""

import asyncio
import functools
import time
import warnings
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from pepperpy.infra.logging import get_logger

# Type variables for function signatures
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")
R = TypeVar("R")

# Logger for this module
logger = get_logger(__name__)


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """Decorator for retrying a function with exponential backoff.

    Args:
        max_retries: The maximum number of retries
        delay: The initial delay between retries
        backoff: The backoff factor
        exceptions: The exceptions to catch

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            current_delay = delay

            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        raise

                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} after error: {str(e)}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

        return cast(F, wrapper)

    return decorator


def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """Decorator for retrying an async function with exponential backoff.

    Args:
        max_retries: The maximum number of retries
        delay: The initial delay between retries
        backoff: The backoff factor
        exceptions: The exceptions to catch

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            current_delay = delay

            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        raise

                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} after error: {str(e)}"
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return cast(F, wrapper)

    return decorator


def deprecated(
    reason: str = "This function is deprecated and will be removed in a future version.",
) -> Callable[[F], F]:
    """Decorator to mark functions as deprecated.

    Args:
        reason: The reason for deprecation

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{func.__name__} is deprecated: {reason}",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def timed(logger_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to log the execution time of a function.

    Args:
        logger_name: Name of the logger to use, defaults to the function's module

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = get_logger(logger_name or func.__module__)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                log.info(f"{func.__name__} executed in {elapsed:.3f} seconds")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                log.error(f"{func.__name__} failed after {elapsed:.3f} seconds: {e}")
                raise

        return cast(F, wrapper)

    return decorator


def async_timed(logger_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to log the execution time of an async function.

    Args:
        logger_name: Name of the logger to use, defaults to the function's module

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = get_logger(logger_name or func.__module__)
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                log.info(f"{func.__name__} executed in {elapsed:.3f} seconds")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                log.error(f"{func.__name__} failed after {elapsed:.3f} seconds: {e}")
                raise

        return cast(F, wrapper)

    return decorator


def memoize(func: F) -> F:
    """Decorator to cache the results of a function.

    Note:
        This is a simple memoization implementation with no expiration or cache size limits.
        For production use cases, consider using the more robust cached decorator from pepperpy.infra.cache.

    Args:
        func: The function to cache

    Returns:
        The decorated function
    """
    cache: Dict[Any, Any] = {}

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Create a key from the arguments
        key = str(args) + str(sorted(kwargs.items()))

        if key not in cache:
            cache[key] = func(*args, **kwargs)

        return cache[key]

    return cast(F, wrapper)


def async_memoize(func: F) -> F:
    """Decorator to cache the results of an async function.

    Note:
        This is a simple memoization implementation with no expiration or cache size limits.
        For production use cases, consider using the more robust async_cached decorator from pepperpy.infra.cache.

    Args:
        func: The function to cache

    Returns:
        The decorated function
    """
    cache: Dict[Any, Any] = {}

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Create a key from the arguments
        key = str(args) + str(sorted(kwargs.items()))

        if key not in cache:
            cache[key] = await func(*args, **kwargs)

        return cache[key]

    return cast(F, wrapper)


def log_exceptions(logger_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to log exceptions raised by a function.

    Args:
        logger_name: Name of the logger to use, defaults to the function's module

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = get_logger(logger_name or func.__module__)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                log.exception(f"Exception in {func.__name__}: {e}")
                raise

        return cast(F, wrapper)

    return decorator


def async_log_exceptions(logger_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to log exceptions raised by an async function.

    Args:
        logger_name: Name of the logger to use, defaults to the function's module

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = get_logger(logger_name or func.__module__)

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log.exception(f"Exception in {func.__name__}: {e}")
                raise

        return cast(F, wrapper)

    return decorator


def validate_arguments(validator: Callable[[Any, Any], bool]) -> Callable[[F], F]:
    """Decorator to validate function arguments.

    Args:
        validator: Function that takes positional arguments and keyword arguments and returns a boolean indicating validity

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not validator(args, kwargs):
                raise ValueError(f"Invalid arguments for {func.__name__}")
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def log_calls(
    log_args: bool = True, log_result: bool = True, logger_name: Optional[str] = None
) -> Callable[[F], F]:
    """Decorator to log function calls.

    Args:
        log_args: Whether to log the function arguments
        log_result: Whether to log the function result
        logger_name: Name of the logger to use, defaults to the function's module

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = get_logger(logger_name or func.__module__)

            if log_args:
                args_str = ", ".join([str(a) for a in args])
                kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
                params = ", ".join(filter(None, [args_str, kwargs_str]))
                log.info(f"Calling {func.__name__}({params})")
            else:
                log.info(f"Calling {func.__name__}")

            result = func(*args, **kwargs)

            if log_result:
                log.info(f"{func.__name__} returned: {result}")
            else:
                log.info(f"{func.__name__} completed")

            return result

        return cast(F, wrapper)

    return decorator


# Export all public decorators
__all__ = [
    "retry",
    "async_retry",
    "deprecated",
    "timed",
    "async_timed",
    "memoize",
    "async_memoize",
    "log_exceptions",
    "async_log_exceptions",
    "validate_arguments",
    "log_calls",
]
