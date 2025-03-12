"""Decorator patterns for cross-cutting concerns.

This module provides decorator patterns for cross-cutting concerns in the PepperPy
framework. Decorators allow for adding behavior to functions and methods without
modifying their code, making them ideal for cross-cutting concerns like logging,
validation, caching, and more.
"""

import functools
import inspect
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic decorators
T = TypeVar("T")  # Return type
F = TypeVar("F", bound=Callable[..., Any])  # Function type


def log_entry_exit(
    level: str = "debug", include_args: bool = True, include_result: bool = True
) -> Callable[[F], F]:
    """Decorator for logging function entry and exit.

    Args:
        level: The logging level to use (debug, info, warning, error, critical)
        include_args: Whether to include function arguments in the log
        include_result: Whether to include the function result in the log

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        func_name = func.__name__
        module_name = func.__module__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            # Log function entry
            entry_message = f"Entering {module_name}.{func_name}"
            if include_args:
                # Format args and kwargs for logging
                args_str = ", ".join([repr(arg) for arg in args])
                kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
                params_str = ", ".join(filter(None, [args_str, kwargs_str]))
                entry_message += f"({params_str})"

            getattr(logger, level)(entry_message)

            # Call the function
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Log function exit
                exit_message = (
                    f"Exiting {module_name}.{func_name} (took {elapsed:.3f}s)"
                )
                if include_result:
                    # Truncate result if it's too long
                    result_str = repr(result)
                    if len(result_str) > 1000:
                        result_str = result_str[:997] + "..."
                    exit_message += f" -> {result_str}"

                getattr(logger, level)(exit_message)
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                getattr(logger, "error")(
                    f"Exception in {module_name}.{func_name} (took {elapsed:.3f}s): {type(e).__name__}: {e}"
                )
                raise

        return cast(F, wrapper)

    return decorator


def validate_args(**validators: Callable[[Any], bool]) -> Callable[[F], F]:
    """Decorator for validating function arguments.

    Args:
        **validators: A mapping of parameter names to validator functions

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function

            Raises:
                PepperpyError: If an argument fails validation
            """
            # Bind the arguments to the function signature
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate the arguments
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise PepperpyError(
                            f"Validation failed for parameter '{param_name}' with value {repr(value)}"
                        )

            # Call the function
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def deprecated(
    message: str = "This function is deprecated and will be removed in a future version.",
    alternative: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator for marking functions as deprecated.

    Args:
        message: The deprecation message
        alternative: The alternative function to use

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        func_name = func.__name__
        module_name = func.__module__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            # Log deprecation warning
            warning_message = (
                f"DEPRECATED: {module_name}.{func_name} is deprecated. {message}"
            )
            if alternative:
                warning_message += f" Use {alternative} instead."
            logger.warning(warning_message)

            # Call the function
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def memoize(
    maxsize: int = 128, typed: bool = False, ttl: Optional[float] = None
) -> Callable[[F], F]:
    """Decorator for memoizing function results.

    Args:
        maxsize: The maximum size of the cache
        typed: Whether to cache different types separately
        ttl: The time-to-live for cache entries, in seconds

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        cache: Dict[Any, Any] = {}
        timestamps: Dict[Any, float] = {}
        hits = 0
        misses = 0

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            nonlocal hits, misses

            # Create a cache key
            key_parts = list(args)
            if typed:
                key_parts.extend([type(arg) for arg in args])
            key_parts.extend(sorted(kwargs.items()))
            if typed:
                key_parts.extend([type(v) for _, v in sorted(kwargs.items())])
            key = hash(tuple(key_parts))

            # Check if the result is in the cache
            if key in cache:
                # Check if the entry has expired
                if ttl is not None and time.time() - timestamps[key] > ttl:
                    # Remove the expired entry
                    del cache[key]
                    del timestamps[key]
                else:
                    hits += 1
                    return cache[key]

            # Call the function
            misses += 1
            result = func(*args, **kwargs)

            # Add the result to the cache
            cache[key] = result
            timestamps[key] = time.time()

            # Limit the cache size
            if maxsize > 0 and len(cache) > maxsize:
                # Remove the oldest entry
                oldest_key = min(timestamps, key=timestamps.get)
                del cache[oldest_key]
                del timestamps[oldest_key]

            return result

        # Add cache statistics to the wrapper
        wrapper.cache_info = lambda: {  # type: ignore
            "hits": hits,
            "misses": misses,
            "size": len(cache),
            "maxsize": maxsize,
        }
        wrapper.cache_clear = lambda: cache.clear()  # type: ignore

        return cast(F, wrapper)

    return decorator


def retry_on_exception(
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    logger_level: str = "warning",
) -> Callable[[F], F]:
    """Decorator for retrying functions on exception.

    Args:
        exceptions: The exception types to catch and retry
        max_retries: The maximum number of retries
        delay: The initial delay between retries, in seconds
        backoff: The backoff factor for increasing the delay
        logger_level: The logging level to use for retry messages

    Returns:
        A decorator function
    """
    exceptions_tuple = exceptions if isinstance(exceptions, tuple) else (exceptions,)

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        func_name = func.__name__
        module_name = func.__module__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
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
                except exceptions_tuple as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        getattr(logger, logger_level)(
                            f"Max retries ({max_retries}) exceeded for {module_name}.{func_name}: {type(e).__name__}: {e}"
                        )
                        raise

                    # Calculate the delay
                    retry_delay = delay * (backoff ** (retry_count - 1))
                    getattr(logger, logger_level)(
                        f"Retry {retry_count}/{max_retries} for {module_name}.{func_name} in {retry_delay:.2f}s: {type(e).__name__}: {e}"
                    )
                    time.sleep(retry_delay)

        return cast(F, wrapper)

    return decorator


def rate_limit(
    calls: int = 10, period: float = 1.0, raise_on_limit: bool = False
) -> Callable[[F], F]:
    """Decorator for rate limiting function calls.

    Args:
        calls: The maximum number of calls allowed in the period
        period: The period in seconds
        raise_on_limit: Whether to raise an exception when the rate limit is exceeded

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        timestamps: List[float] = []

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function

            Raises:
                PepperpyError: If the rate limit is exceeded and raise_on_limit is True
            """
            now = time.time()

            # Remove timestamps older than the period
            while timestamps and now - timestamps[0] > period:
                timestamps.pop(0)

            # Check if the rate limit is exceeded
            if len(timestamps) >= calls:
                if raise_on_limit:
                    raise PepperpyError(
                        f"Rate limit exceeded: {calls} calls per {period} seconds"
                    )
                # Wait until the oldest timestamp is outside the period
                sleep_time = timestamps[0] + period - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    now = time.time()
                    # Remove timestamps older than the period
                    while timestamps and now - timestamps[0] > period:
                        timestamps.pop(0)

            # Add the current timestamp
            timestamps.append(now)

            # Call the function
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def trace(
    level: str = "debug", include_locals: bool = True, max_depth: int = 10
) -> Callable[[F], F]:
    """Decorator for tracing function execution.

    Args:
        level: The logging level to use (debug, info, warning, error, critical)
        include_locals: Whether to include local variables in the trace
        max_depth: The maximum depth of the stack trace

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        func_name = func.__name__
        module_name = func.__module__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            # Log function entry
            getattr(logger, level)(f"TRACE: Entering {module_name}.{func_name}")

            # Get the current stack
            stack = traceback.extract_stack()
            stack = stack[:-2]  # Remove this function and the decorator from the stack
            stack = stack[-max_depth:] if len(stack) > max_depth else stack

            # Log the stack trace
            for i, frame in enumerate(stack):
                frame_file, frame_line, frame_func, frame_text = frame
                getattr(logger, level)(
                    f"TRACE: [{i}] {frame_file}:{frame_line} in {frame_func}: {frame_text}"
                )

            # Log local variables
            if include_locals:
                frame = inspect.currentframe()
                if frame:
                    try:
                        # Get the frame of the decorated function
                        frame = frame.f_back
                        if frame:
                            # Get the local variables
                            local_vars = frame.f_locals
                            # Log the local variables
                            for name, value in local_vars.items():
                                if name != "func":  # Skip the function itself
                                    value_str = repr(value)
                                    if len(value_str) > 1000:
                                        value_str = value_str[:997] + "..."
                                    getattr(logger, level)(
                                        f"TRACE: Local variable {name} = {value_str}"
                                    )
                    finally:
                        del frame  # Avoid reference cycles

            # Call the function
            try:
                result = func(*args, **kwargs)
                getattr(logger, level)(f"TRACE: Exiting {module_name}.{func_name}")
                return result
            except Exception as e:
                getattr(logger, level)(
                    f"TRACE: Exception in {module_name}.{func_name}: {type(e).__name__}: {e}"
                )
                raise

        return cast(F, wrapper)

    return decorator


def validate_return(
    validator: Callable[[Any], bool], error_message: str = "Invalid return value"
) -> Callable[[F], F]:
    """Decorator for validating function return values.

    Args:
        validator: A function that validates the return value
        error_message: The error message to use if validation fails

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function

            Raises:
                PepperpyError: If the return value fails validation
            """
            result = func(*args, **kwargs)
            if not validator(result):
                raise PepperpyError(f"{error_message}: {repr(result)}")
            return result

        return cast(F, wrapper)

    return decorator


def profile(
    level: str = "debug", threshold: Optional[float] = None
) -> Callable[[F], F]:
    """Decorator for profiling function execution time.

    Args:
        level: The logging level to use (debug, info, warning, error, critical)
        threshold: The threshold in seconds above which to log the execution time

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        func_name = func.__name__
        module_name = func.__module__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.time() - start_time
                if threshold is None or elapsed >= threshold:
                    getattr(logger, level)(
                        f"PROFILE: {module_name}.{func_name} took {elapsed:.6f} seconds"
                    )

        return cast(F, wrapper)

    return decorator


def synchronized(lock: Optional[Any] = None) -> Callable[[F], F]:
    """Decorator for synchronizing function execution.

    Args:
        lock: The lock to use for synchronization, or None to create a new lock

    Returns:
        A decorator function
    """
    import threading

    # Create a lock if one is not provided
    actual_lock = lock or threading.RLock()

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            with actual_lock:
                return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def timeout(seconds: float) -> Callable[[F], F]:
    """Decorator for timing out function execution.

    Args:
        seconds: The timeout in seconds

    Returns:
        A decorator function
    """
    import signal

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function

            Raises:
                PepperpyError: If the function times out
            """

            # Define a handler for the alarm signal
            def handler(signum: int, frame: Any) -> None:
                raise PepperpyError(f"Function timed out after {seconds} seconds")

            # Set the alarm signal handler
            old_handler = signal.signal(signal.SIGALRM, handler)
            # Set the alarm
            signal.setitimer(signal.ITIMER_REAL, seconds)
            try:
                # Call the function
                return func(*args, **kwargs)
            finally:
                # Cancel the alarm
                signal.setitimer(signal.ITIMER_REAL, 0)
                # Restore the old handler
                signal.signal(signal.SIGALRM, old_handler)

        return cast(F, wrapper)

    return decorator
