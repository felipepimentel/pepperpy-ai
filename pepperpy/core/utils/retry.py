"""Utility functions for retrying operations."""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Optional, Sequence, Tuple, Type, TypeVar, Union, cast, overload

logger = logging.getLogger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])
ExceptionType = Union[Type[Exception], Sequence[Type[Exception]]]

@overload
def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Optional[ExceptionType] = None,
) -> Callable[[F], F]:
    ...

@overload
def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Optional[ExceptionType] = None,
) -> Callable[[AsyncF], AsyncF]:
    ...

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Optional[ExceptionType] = None,
) -> Callable[[F], F]:
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
        exceptions = (Exception,)
    elif not isinstance(exceptions, (tuple, list)):
        exceptions = (exceptions,)  # type: ignore

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
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

            return None

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
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

            return None

        return cast(F, async_wrapper if asyncio.iscoroutinefunction(func) else wrapper)

    return decorator 