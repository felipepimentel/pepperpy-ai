"""
Core decorators for PepperPy.

This module provides decorators for common patterns used throughout PepperPy.
"""

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar, cast

from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def handle_provider_errors(
    error_type: type[PepperpyError] = PepperpyError,
    log_level: str = "error",
    reraise: bool = True,
) -> Callable[[F], F]:
    """Decorator to handle provider method errors consistently.

    Wraps a method to catch exceptions and handle them according to the provider
    error handling pattern:
    1. Log the error with appropriate context
    2. Convert to domain-specific error type if needed
    3. Optionally reraise or return None

    Args:
        error_type: Error type to convert exceptions to
        log_level: Logging level to use
        reraise: Whether to reraise the error or return None

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            provider_name = self.__class__.__name__
            method_name = func.__name__

            try:
                return await func(self, *args, **kwargs)
            except error_type:
                # Don't wrap if it's already the correct type
                if reraise:
                    raise
                if hasattr(self, "logger"):
                    getattr(self.logger, log_level)(
                        f"Error in {provider_name}.{method_name}", exc_info=True
                    )
                return None
            except Exception as e:
                # Get a more specific message that includes the provider type
                message = f"Error in {provider_name}.{method_name}: {e}"

                # Log with appropriate level
                if hasattr(self, "logger"):
                    getattr(self.logger, log_level)(message, exc_info=True)
                else:
                    getattr(logger, log_level)(message, exc_info=True)

                if reraise:
                    raise error_type(message) from e
                return None

        @functools.wraps(func)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            provider_name = self.__class__.__name__
            method_name = func.__name__

            try:
                return func(self, *args, **kwargs)
            except error_type:
                # Don't wrap if it's already the correct type
                if reraise:
                    raise
                if hasattr(self, "logger"):
                    getattr(self.logger, log_level)(
                        f"Error in {provider_name}.{method_name}", exc_info=True
                    )
                return None
            except Exception as e:
                # Get a more specific message that includes the provider type
                message = f"Error in {provider_name}.{method_name}: {e}"

                # Log with appropriate level
                if hasattr(self, "logger"):
                    getattr(self.logger, log_level)(message, exc_info=True)
                else:
                    getattr(logger, log_level)(message, exc_info=True)

                if reraise:
                    raise error_type(message) from e
                return None

        # Use correct wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator


def validate_initialization(
    error_type: type[PepperpyError] = PepperpyError,
) -> Callable[[F], F]:
    """Decorator to validate provider is initialized before method execution.

    Ensures that a provider's initialize method has been called before
    executing other methods.

    Args:
        error_type: Error type to raise if not initialized

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            if not getattr(self, "initialized", False):
                raise error_type(
                    f"Provider {self.__class__.__name__} must be initialized "
                    f"before calling {func.__name__}"
                )
            return await func(self, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            if not getattr(self, "initialized", False):
                raise error_type(
                    f"Provider {self.__class__.__name__} must be initialized "
                    f"before calling {func.__name__}"
                )
            return func(self, *args, **kwargs)

        # Use correct wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator


def with_timing(log_level: str = "debug") -> Callable[[F], F]:
    """Decorator to log timing information for method execution.

    Args:
        log_level: Logging level to use

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            provider_name = self.__class__.__name__
            method_name = func.__name__

            start_time = time.monotonic()
            try:
                return await func(self, *args, **kwargs)
            finally:
                duration = time.monotonic() - start_time
                if hasattr(self, "logger"):
                    getattr(self.logger, log_level)(
                        f"{provider_name}.{method_name} took {duration:.4f}s"
                    )
                else:
                    getattr(logger, log_level)(
                        f"{provider_name}.{method_name} took {duration:.4f}s"
                    )

        @functools.wraps(func)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            provider_name = self.__class__.__name__
            method_name = func.__name__

            start_time = time.monotonic()
            try:
                return func(self, *args, **kwargs)
            finally:
                duration = time.monotonic() - start_time
                if hasattr(self, "logger"):
                    getattr(self.logger, log_level)(
                        f"{provider_name}.{method_name} took {duration:.4f}s"
                    )
                else:
                    getattr(logger, log_level)(
                        f"{provider_name}.{method_name} took {duration:.4f}s"
                    )

        # Use correct wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
    error_type: type[PepperpyError] | None = None,
) -> Callable[[F], F]:
    """Decorator to retry a function on failure.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff_factor: Factor to increase delay on each attempt
        retry_exceptions: Exception types to retry on
        error_type: Error type to convert exceptions to after all retries

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            provider_name = self.__class__.__name__
            method_name = func.__name__
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(self, *args, **kwargs)
                except retry_exceptions as e:
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        if error_type:
                            message = (
                                f"Failed to execute {provider_name}.{method_name} "
                                f"after {max_attempts} attempts: {e}"
                            )
                            if hasattr(self, "logger"):
                                self.logger.error(message)
                            else:
                                logger.error(message)
                            raise error_type(message) from e
                        raise

                    # Log retry
                    if hasattr(self, "logger"):
                        self.logger.warning(
                            f"Retrying {provider_name}.{method_name} "
                            f"after error: {e} (attempt {attempt + 1}/{max_attempts})"
                        )
                    else:
                        logger.warning(
                            f"Retrying {provider_name}.{method_name} "
                            f"after error: {e} (attempt {attempt + 1}/{max_attempts})"
                        )

                    # Wait before retrying
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor

        @functools.wraps(func)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            provider_name = self.__class__.__name__
            method_name = func.__name__
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(self, *args, **kwargs)
                except retry_exceptions as e:
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        if error_type:
                            message = (
                                f"Failed to execute {provider_name}.{method_name} "
                                f"after {max_attempts} attempts: {e}"
                            )
                            if hasattr(self, "logger"):
                                self.logger.error(message)
                            else:
                                logger.error(message)
                            raise error_type(message) from e
                        raise

                    # Log retry
                    if hasattr(self, "logger"):
                        self.logger.warning(
                            f"Retrying {provider_name}.{method_name} "
                            f"after error: {e} (attempt {attempt + 1}/{max_attempts})"
                        )
                    else:
                        logger.warning(
                            f"Retrying {provider_name}.{method_name} "
                            f"after error: {e} (attempt {attempt + 1}/{max_attempts})"
                        )

                    # Wait before retrying
                    time.sleep(current_delay)
                    current_delay *= backoff_factor

        # Use correct wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator
