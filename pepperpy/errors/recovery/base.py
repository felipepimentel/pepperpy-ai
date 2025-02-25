"""Base classes for error recovery strategies.

This module provides the core error recovery functionality, including:
- Abstract recovery strategy interface
- Common recovery strategies (retry, fallback)
- Recovery strategy registry

Example:
    >>> strategy = RetryStrategy(max_retries=3, delay=1.0)
    >>> error = ResourceError("Resource locked")
    >>> strategy.recover(error)
    True
"""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable

from ..base import ResourceError, StateError

logger = logging.getLogger(__name__)


class RecoveryStrategy(ABC):
    """Abstract base class for error recovery strategies.

    Example:
        >>> class MyStrategy(RecoveryStrategy):
        ...     def can_recover(self, error):
        ...         return isinstance(error, ResourceError)
        ...     def recover(self, error):
        ...         return retry_operation()
    """

    @abstractmethod
    def can_recover(self, error: Exception) -> bool:
        """Check if this strategy can recover from the given error.

        Args:
            error: The error to check

        Returns:
            bool: True if recovery is possible
        """
        pass

    @abstractmethod
    def recover(self, error: Exception) -> bool:
        """Attempt to recover from the error.

        Args:
            error: The error to recover from

        Returns:
            bool: True if recovery was successful

        Raises:
            Any: Implementation may raise additional errors
        """
        pass


class RetryStrategy(RecoveryStrategy):
    """Recovery strategy that retries the operation with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay by after each retry
        operation: Optional function to retry

    Example:
        >>> strategy = RetryStrategy(max_retries=3, delay=1.0)
        >>> error = ResourceError("Resource locked")
        >>> strategy.recover(error)
        True
    """

    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        operation: Callable | None = None,
    ):
        """Initialize a new retry strategy."""
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.operation = operation

    def can_recover(self, error: Exception) -> bool:
        """Check if the error is recoverable via retry."""
        return isinstance(error, (ResourceError, StateError))

    def recover(self, error: Exception) -> bool:
        """Attempt to recover by retrying the operation.

        Args:
            error: The error to recover from

        Returns:
            bool: True if recovery was successful

        Example:
            >>> strategy = RetryStrategy(operation=lambda: fetch_resource())
            >>> strategy.recover(ResourceError("Timeout"))
            True
        """
        current_delay = self.delay
        for attempt in range(self.max_retries):
            try:
                if self.operation:
                    self.operation()
                return True
            except Exception as e:
                logger.warning(
                    f"Retry attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                time.sleep(current_delay)
                current_delay *= self.backoff_factor
        return False


class FallbackStrategy(RecoveryStrategy):
    """Recovery strategy that tries alternative approaches.

    Args:
        alternatives: List of alternative functions to try

    Example:
        >>> strategy = FallbackStrategy([
        ...     lambda: primary_operation(),
        ...     lambda: backup_operation()
        ... ])
        >>> strategy.recover(error)
        True
    """

    def __init__(self, alternatives: list[Callable]):
        """Initialize a new fallback strategy."""
        self.alternatives = alternatives

    def can_recover(self, error: Exception) -> bool:
        """Check if fallback recovery is possible."""
        return bool(self.alternatives)

    def recover(self, error: Exception) -> bool:
        """Attempt recovery using alternative approaches.

        Args:
            error: The error to recover from

        Returns:
            bool: True if any alternative succeeded
        """
        for i, alternative in enumerate(self.alternatives):
            try:
                alternative()
                return True
            except Exception as e:
                logger.warning(
                    f"Fallback attempt {i + 1}/{len(self.alternatives)} failed: {e}"
                )
        return False


class RecoveryRegistry:
    """Registry for recovery strategies.

    Example:
        >>> registry = RecoveryRegistry()
        >>> strategy = RetryStrategy()
        >>> registry.register(ResourceError, strategy)
        >>> registry.attempt_recovery(error)
        True
    """

    def __init__(self):
        """Initialize a new recovery registry."""
        self._strategies: dict[type[Exception], list[RecoveryStrategy]] = {}

    def register(self, error_type: type[Exception], strategy: RecoveryStrategy):
        """Register a recovery strategy for an error type.

        Args:
            error_type: The type of error
            strategy: The strategy to register
        """
        if error_type not in self._strategies:
            self._strategies[error_type] = []
        self._strategies[error_type].append(strategy)

    def get_strategies(self, error_type: type[Exception]) -> list[RecoveryStrategy]:
        """Get all recovery strategies for an error type.

        Args:
            error_type: The type of error

        Returns:
            List[RecoveryStrategy]: List of applicable strategies
        """
        strategies = []
        for t in error_type.__mro__:
            if t in self._strategies:
                strategies.extend(self._strategies[t])
        return strategies

    def attempt_recovery(self, error: Exception) -> bool:
        """Attempt to recover from an error using registered strategies.

        Args:
            error: The error to recover from

        Returns:
            bool: True if recovery was successful
        """
        strategies = self.get_strategies(type(error))
        for strategy in strategies:
            try:
                if strategy.can_recover(error):
                    if strategy.recover(error):
                        return True
            except Exception as e:
                logger.error(
                    f"Recovery strategy {strategy.__class__.__name__} failed: {e}"
                )
        return False


# Global recovery registry
global_recovery_registry = RecoveryRegistry()
