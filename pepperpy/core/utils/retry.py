"""Utility functions for retrying operations."""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Optional, Sequence, Type, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Optional[Union[Type[Exception], Sequence[Type[Exception]]]] = None,
) -> Callable:
    """Decorator for retrying operations that may fail.

    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between attempts in seconds.
        backoff: Multiplier for delay between attempts.
        exceptions: Exception types to catch and retry.
            If None, retries on any Exception.

    Returns:
        Decorator function.

    Example:
        >>> @retry(max_attempts=3, delay=1.0, backoff=2.0)
        ... def fetch_data():
        ...     # May raise an exception
        ...     return requests.get("http://example.com")
    """
    if exceptions is None:
        exceptions = Exception
    elif not isinstance(exceptions, (tuple, list)):
        exceptions = (exceptions,)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:  # type: ignore
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                            f"Retrying in {current_delay:.1f} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed. "
                            f"Last error: {str(e)}"
                        )

            if last_exception is not None:
                raise last_exception

            return None  # type: ignore

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:  # type: ignore
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                            f"Retrying in {current_delay:.1f} seconds..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed. "
                            f"Last error: {str(e)}"
                        )

            if last_exception is not None:
                raise last_exception

            return None  # type: ignore

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator 