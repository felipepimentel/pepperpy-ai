"""Error recovery strategies.

This module provides strategies for recovering from errors.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from pepperpy.common.errors.unified import PepperError

T = TypeVar("T")


class ErrorRecoveryStrategy(ABC):
    """Base class for error recovery strategies."""

    @abstractmethod
    def recover(
        self, error: Exception, operation: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        """Attempt to recover from an error.

        Args:
            error: The error to recover from
            operation: The operation that failed
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the recovery attempt

        Raises:
            Exception: If recovery fails
        """
        pass


class RetryStrategy(ErrorRecoveryStrategy):
    """Strategy that retries the operation."""

    def __init__(self, max_attempts: int = 3, delay: float = 1.0) -> None:
        """Initialize retry strategy.

        Args:
            max_attempts: Maximum number of retry attempts
            delay: Delay between attempts in seconds
        """
        self.max_attempts = max_attempts
        self.delay = delay

    def recover(
        self, error: Exception, operation: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        """Retry the operation up to max_attempts times.

        Args:
            error: The error to recover from
            operation: The operation to retry
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of a successful retry

        Raises:
            Exception: If all retries fail
        """
        import time

        attempts = 1
        last_error = error

        while attempts < self.max_attempts:
            try:
                time.sleep(self.delay)
                return operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                attempts += 1

        raise last_error


class FallbackStrategy(ErrorRecoveryStrategy):
    """Strategy that provides a fallback value or operation."""

    def __init__(self, fallback: Callable[..., T] | T) -> None:
        """Initialize fallback strategy.

        Args:
            fallback: Fallback value or function
        """
        self.fallback = fallback

    def recover(
        self, error: Exception, operation: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        """Return fallback value or execute fallback operation.

        Args:
            error: The error to recover from
            operation: The original operation
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The fallback value or result
        """
        if callable(self.fallback):
            return self.fallback(*args, **kwargs)
        return self.fallback


__all__ = ["ErrorRecoveryStrategy", "FallbackStrategy", "PepperError", "RetryStrategy"]
