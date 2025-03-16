"""Core utilities for PepperPy.

This module provides core utility functions and classes used throughout the
PepperPy framework, including logging, decorators, context managers, and more.
"""

import contextlib
import functools
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

# ---- Type Variables ----

# Type variables for generic utilities
T = TypeVar("T")  # Input/value type
R = TypeVar("R")  # Result/return type
K = TypeVar("K")  # Key type
F = TypeVar("F", bound=Callable[..., Any])  # Function type

# ---- Logging Utilities ----

# Cache of loggers
_loggers: Dict[str, logging.Logger] = {}

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging(
    level: Optional[Union[int, str]] = None,
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True,
) -> None:
    """Configure the logging system.

    This should be called once at the start of your application.

    Args:
        level: The log level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        format_string: The format string for log messages
        log_file: The path to the log file
        console: Whether to log to the console
    """
    # Convert string level to int if needed
    numeric_level: int
    if level is None:
        # Get level from environment variable or default to INFO
        level_str = os.environ.get("PEPPERPY_LOG_LEVEL", "INFO")
        numeric_level = getattr(logging, level_str.upper(), logging.INFO)
    elif isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
    else:
        numeric_level = level

    # Get format string from environment variable or use default
    if format_string is None:
        format_string = os.environ.get("PEPPERPY_LOG_FORMAT", DEFAULT_LOG_FORMAT)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if requested
    if log_file:
        # Create directory if it doesn't exist
        log_path = Path(log_file)
        if not log_path.parent.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    If a logger with the given name already exists, it will be returned.
    Otherwise, a new logger will be created.

    Args:
        name: The name of the logger

    Returns:
        The logger
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger


def set_log_level(level: Union[int, str], logger_name: Optional[str] = None) -> None:
    """Set the log level for a logger.

    Args:
        level: The log level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        logger_name: The name of the logger, or None for the root logger
    """
    # Convert string level to int if needed
    numeric_level: int
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
    else:
        numeric_level = level

    # Get the logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    logger.setLevel(numeric_level)


# ---- Decorator Utilities ----


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
        logger = get_logger(module_name)
        log_func = getattr(logger, level.lower())

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
            if include_args:
                arg_str = ", ".join(
                    [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()]
                )
                log_func(f"Entering {func_name}({arg_str})")
            else:
                log_func(f"Entering {func_name}")

            # Call the function
            try:
                result = func(*args, **kwargs)
                # Log function exit
                if include_result:
                    log_func(f"Exiting {func_name} -> {result}")
                else:
                    log_func(f"Exiting {func_name}")
                return result
            except Exception as e:
                log_func(f"Exception in {func_name}: {e}")
                raise

        return cast(F, wrapper)

    return decorator


def memoize(
    maxsize: int = 128, typed: bool = False, ttl: Optional[float] = None
) -> Callable[[F], F]:
    """Decorator for memoizing function results.

    Args:
        maxsize: Maximum size of the cache
        typed: Whether to cache based on argument types
        ttl: Time-to-live for cache entries (in seconds)

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
        cache: Dict[Any, Tuple[Any, float]] = {}
        func_name = func.__name__
        logger = get_logger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            # Create a key for the cache
            key_parts = list(args)
            if typed:
                key_parts.extend([type(arg) for arg in args])

            # Sort kwargs by key to ensure consistent ordering
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(sorted_kwargs)
            if typed:
                key_parts.extend([type(v) for _, v in sorted_kwargs])

            key = tuple(key_parts)

            # Check if the result is in the cache
            now = time.time()
            if key in cache:
                result, timestamp = cache[key]
                # Check if the result is still valid
                if ttl is None or now - timestamp < ttl:
                    logger.debug(f"Cache hit for {func_name}")
                    return result
                logger.debug(f"Cache expired for {func_name}")
            else:
                logger.debug(f"Cache miss for {func_name}")

            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache[key] = (result, now)

            # Limit the cache size
            if maxsize > 0 and len(cache) > maxsize:
                # Remove the oldest entry
                oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                del cache[oldest_key]

            return result

        return cast(F, wrapper)

    return decorator


def retry_on_exception(
    exceptions: Union[Type[BaseException], List[Type[BaseException]]] = Exception,
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
    # Convert to tuple for isinstance check
    if isinstance(exceptions, list):
        exceptions_tuple = tuple(exceptions)
    elif not isinstance(exceptions, tuple):
        exceptions_tuple = (exceptions,)
    else:
        exceptions_tuple = exceptions

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        func_name = func.__name__
        logger = get_logger(func.__module__)
        log_func = getattr(logger, logger_level.lower())

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions_tuple as e:
                    last_exception = e
                    if attempt < max_retries:
                        log_func(
                            f"Attempt {attempt + 1}/{max_retries + 1} for {func_name} "
                            f"failed with {type(e).__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        log_func(
                            f"All {max_retries + 1} attempts for {func_name} failed. "
                            f"Last error: {type(e).__name__}: {e}"
                        )

            # If we get here, all retries failed
            assert last_exception is not None
            raise last_exception

        return cast(F, wrapper)

    return decorator


def profile(
    level: str = "debug", threshold: Optional[float] = None
) -> Callable[[F], F]:
    """Decorator for profiling function execution time.

    Args:
        level: The logging level to use
        threshold: Only log if execution time exceeds this threshold (in seconds)

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
        logger = get_logger(func.__module__)
        log_func = getattr(logger, level.lower())

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
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_time = time.time() - start_time
                if threshold is None or elapsed_time >= threshold:
                    log_func(f"{func_name} took {elapsed_time:.6f}s to execute")

        return cast(F, wrapper)

    return decorator


# ---- Context Manager Utilities ----


@contextlib.contextmanager
def timed_context(name: str = "operation") -> Iterator["TimedContext"]:
    """Context manager for timing operations.

    Args:
        name: The name of the operation

    Yields:
        A TimedContext object
    """
    context = TimedContext(name)
    try:
        context.__enter__()
        yield context
    finally:
        context.__exit__(None, None, None)


class TimedContext:
    """Context manager for timing operations.

    This class provides a context manager for timing operations.
    """

    def __init__(self, name: str = "operation"):
        """Initialize the timed context.

        Args:
            name: The name of the operation
        """
        self._name = name
        self._start_time = 0.0
        self._end_time = 0.0

    def __enter__(self) -> "TimedContext":
        """Enter the context.

        Returns:
            The context object
        """
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context.

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
        if self._end_time > 0:
            return self._end_time - self._start_time
        return time.time() - self._start_time

    @property
    def name(self) -> str:
        """Get the name of the operation.

        Returns:
            The name of the operation
        """
        return self._name


@contextlib.contextmanager
def retry_context(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
) -> Iterator["RetryContext"]:
    """Context manager for retrying operations.

    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries (in seconds)
        backoff: Backoff factor for the delay
        exceptions: The exception(s) to catch and retry on

    Yields:
        A RetryContext object
    """
    context = RetryContext(max_retries, delay, backoff, exceptions)
    try:
        context.__enter__()
        yield context
    except Exception as e:
        if not context.__exit__(type(e), e, traceback.extract_tb(sys.exc_info()[2])):
            raise
    else:
        context.__exit__(None, None, None)


class RetryContext:
    """Context manager for retrying operations.

    This class provides a context manager for retrying operations that may fail.
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
            max_retries: Maximum number of retries
            delay: Initial delay between retries (in seconds)
            backoff: Backoff factor for the delay
            exceptions: The exception(s) to catch and retry on
        """
        self._max_retries = max_retries
        self._delay = delay
        self._backoff = backoff
        self._exceptions = exceptions
        self._retry_count = 0
        self._last_exception: Optional[Exception] = None

    def __enter__(self) -> "RetryContext":
        """Enter the context.

        Returns:
            The context object
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Exit the context.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised

        Returns:
            True if the exception was handled, False otherwise
        """
        if exc_type is None:
            return False

        # Check if the exception is one we should retry on
        if isinstance(self._exceptions, list):
            if not any(isinstance(exc_val, exc_type) for exc_type in self._exceptions):
                return False
        else:
            if not isinstance(exc_val, self._exceptions):
                return False

        # Store the exception
        self._last_exception = exc_val

        # Check if we've reached the maximum number of retries
        if self._retry_count >= self._max_retries:
            return False

        # Increment the retry count
        self._retry_count += 1

        # Sleep before the next retry
        current_delay = self._delay * (self._backoff ** (self._retry_count - 1))
        time.sleep(current_delay)

        # Indicate that we've handled the exception
        return True

    @property
    def retry_count(self) -> int:
        """Get the number of retries.

        Returns:
            The number of retries
        """
        return self._retry_count

    @property
    def last_exception(self) -> Optional[Exception]:
        """Get the last exception.

        Returns:
            The last exception, or None if no exception has been caught
        """
        return self._last_exception


# ---- Chainable API Utilities ----


class ChainableMethod(Generic[T, R]):
    """Chainable method wrapper.

    This class wraps a method to make it chainable, allowing it to be composed
    with other methods in a pipeline.
    """

    def __init__(
        self,
        func: Callable[[T], R],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize the chainable method.

        Args:
            func: The function to wrap
            name: Optional name for the method
            description: Optional description of what the method does
        """
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self._next: Optional[ChainableMethod] = None

    def __call__(self, value: T) -> Union[R, Any]:
        """Call the method with the given value.

        Args:
            value: The input value

        Returns:
            The result of the method, or the result of the next method in the chain
        """
        result = self.func(value)
        if self._next is not None:
            return self._next(result)
        return result

    def then(self, next_method: "ChainableMethod") -> "ChainableMethod":
        """Chain this method with another method.

        Args:
            next_method: The next method in the chain

        Returns:
            The next method, for further chaining
        """
        self._next = next_method
        return next_method


def chainable(
    name: Optional[str] = None, description: Optional[str] = None
) -> Callable[[F], F]:
    """Decorator for creating chainable methods.

    Args:
        name: The name of the chainable method
        description: The description of the chainable method

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
            """
            # Create a chainable method
            method: ChainableMethod = ChainableMethod(
                lambda x: func(x, *args, **kwargs), name, description
            )
            return method

        return cast(F, wrapper)

    return decorator


class Pipeline(Generic[T, R]):
    """Pipeline for chaining operations.

    This class provides a pipeline for chaining operations together.
    """

    def __init__(self, name: str):
        """Initialize the pipeline.

        Args:
            name: The name of the pipeline
        """
        self._name = name
        self._steps: List[ChainableMethod] = []
        self._metadata: Dict[str, Any] = {}

    def add_step(self, step: ChainableMethod) -> "Pipeline[T, R]":
        """Add a step to the pipeline.

        Args:
            step: The step to add

        Returns:
            The pipeline, for method chaining
        """
        self._steps.append(step)
        return self

    def with_metadata(self, key: str, value: Any) -> "Pipeline[T, R]":
        """Add metadata to the pipeline.

        Args:
            key: The metadata key
            value: The metadata value

        Returns:
            The pipeline, for method chaining
        """
        self._metadata[key] = value
        return self

    def execute(self, input_value: T) -> R:
        """Execute the pipeline.

        Args:
            input_value: The input value to the pipeline

        Returns:
            The result of the pipeline
        """
        if not self._steps:
            raise ValueError("Pipeline has no steps")

        # Chain the steps together
        current_step = self._steps[0]
        for step in self._steps[1:]:
            current_step.then(step)

        # Execute the pipeline
        return cast(R, current_step(input_value))


def create_pipeline(name: str) -> Pipeline[Any, Any]:
    """Create a new pipeline.

    Args:
        name: The name of the pipeline

    Returns:
        A new pipeline
    """
    return Pipeline(name)
