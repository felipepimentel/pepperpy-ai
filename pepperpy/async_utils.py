"""Asynchronous utilities for the PepperPy framework.

This module provides specialized utilities for asynchronous programming,
including concurrency control, retry mechanisms, timeouts, and cancellation support.
All async-related functionality is consolidated here to avoid fragmentation.
"""

import asyncio
import contextlib
from typing import Any, Awaitable, Callable, Coroutine, List, Optional, TypeVar, Union

from pepperpy.core.errors import PepperPyError

T = TypeVar("T")
U = TypeVar("U")


# Error classes
class TimeoutError(PepperPyError):
    """Raised when an operation times out."""

    pass


# Concurrency utilities
async def gather_with_concurrency(
    limit: int, *tasks: Awaitable[T], return_exceptions: bool = False
) -> List[Union[T, BaseException]] if return_exceptions else List[T]:
    """Run tasks with a concurrency limit."""
    semaphore = asyncio.Semaphore(limit)

    async def semaphore_task(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task

    return await asyncio.gather(
        *(semaphore_task(task) for task in tasks), return_exceptions=return_exceptions
    )


async def with_timeout(
    awaitable: Awaitable[T], timeout: float, message: Optional[str] = None
) -> T:
    """Run an awaitable with a timeout."""
    try:
        return await asyncio.wait_for(awaitable, timeout)
    except asyncio.TimeoutError:
        error_msg = message or f"Operation timed out after {timeout} seconds"
        raise TimeoutError(error_msg)


@contextlib.asynccontextmanager
async def cancellation_scope():
    """Context manager that can be used to cancel a group of tasks."""
    tasks: List[asyncio.Task] = []

    class Scope:
        def create_task(self, coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
            task = asyncio.create_task(coro)
            tasks.append(task)
            return task

    scope = Scope()

    try:
        yield scope
    finally:
        # Cancel all pending tasks
        for task in tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Retry mechanism
class RetryPolicy:
    """Configuration for retry behavior."""

    def __init__(
        self,
        attempts: int = 3,
        delay: float = 0.1,
        max_delay: Optional[float] = None,
        backoff_factor: float = 2.0,
        retry_on: Optional[List[type]] = None,
    ):
        """Initialize a retry policy.

        Args:
            attempts: Maximum number of attempts
            delay: Initial delay between attempts in seconds
            max_delay: Maximum delay between attempts in seconds
            backoff_factor: Factor to multiply delay by after each attempt
            retry_on: List of exception types to retry on
        """
        self.attempts = attempts
        self.delay = delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retry_on = retry_on or [Exception]


def retry_policy(**kwargs) -> RetryPolicy:
    """Create a retry policy with the specified configuration."""
    return RetryPolicy(**kwargs)


async def async_retry(
    coro_func: Callable[..., Awaitable[T]],
    *args,
    policy: Optional[RetryPolicy] = None,
    **kwargs,
) -> T:
    """Execute a coroutine function with retries."""
    policy = policy or RetryPolicy()
    last_exception = None
    current_delay = policy.delay

    for attempt in range(1, policy.attempts + 1):
        try:
            return await coro_func(*args, **kwargs)
        except tuple(policy.retry_on) as e:
            last_exception = e

            if attempt < policy.attempts:
                await asyncio.sleep(current_delay)

                # Update delay for next attempt
                current_delay *= policy.backoff_factor
                if policy.max_delay is not None:
                    current_delay = min(current_delay, policy.max_delay)

    # All attempts failed
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry failed but no exception was caught")


# Public API
__all__ = [
    # Errors
    "TimeoutError",
    # Concurrency
    "gather_with_concurrency",
    "with_timeout",
    "cancellation_scope",
    # Retry
    "async_retry",
    "retry_policy",
    "RetryPolicy",
]
