"""Decorators for PepperPy.

This module provides decorators for common patterns in PepperPy.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from pepperpy.utils.logging import get_logger

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
                        raise e

                    logger.warning(
                        f"Retrying {func.__name__} after error: {str(e)}. "
                        f"Retry {retries}/{max_retries} in {current_delay:.2f}s"
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
            import asyncio

            retries = 0
            current_delay = delay

            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        raise e

                    logger.warning(
                        f"Retrying {func.__name__} after error: {str(e)}. "
                        f"Retry {retries}/{max_retries} in {current_delay:.2f}s"
                    )

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return cast(F, wrapper)

    return decorator


def deprecated(
    reason: str = "This function is deprecated and will be removed in a future version.",
) -> Callable[[F], F]:
    """Decorator for marking a function as deprecated.

    Args:
        reason: The reason for deprecation

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.warning(f"{func.__name__} is deprecated: {reason}")
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def timed(logger_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator for timing a function.

    Args:
        logger_name: The name of the logger to use, or None to use the module logger

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger_to_use = get_logger(logger_name) if logger_name else logger

            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()

            logger_to_use.info(
                f"{func.__name__} took {end_time - start_time:.2f}s to execute"
            )

            return result

        return cast(F, wrapper)

    return decorator


def async_timed(logger_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator for timing an async function.

    Args:
        logger_name: The name of the logger to use, or None to use the module logger

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger_to_use = get_logger(logger_name) if logger_name else logger

            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()

            logger_to_use.info(
                f"{func.__name__} took {end_time - start_time:.2f}s to execute"
            )

            return result

        return cast(F, wrapper)

    return decorator


def memoize(func: F) -> F:
    """Decorator for memoizing a function.

    Args:
        func: The function to memoize

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
    """Decorator for memoizing an async function.

    Args:
        func: The function to memoize

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
