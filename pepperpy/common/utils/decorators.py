"""Decorator utilities for Pepperpy."""

import asyncio
import functools
import inspect
import logging
import time
from typing import Any, Callable, Optional, TypeVar, Union, cast

from ..errors import PepperpyError

T = TypeVar("T", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,)
) -> Callable[[T], T]:
    """Retry decorator for handling transient failures.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay between retries
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Decorated function
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    if attempt > 0:
                        logger.debug(
                            f"Retrying {func.__name__} (attempt {attempt + 1}/{max_attempts})"
                        )
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    continue
                except Exception as e:
                    raise PepperpyError(
                        f"Unhandled error in {func.__name__}: {str(e)}"
                    ) from e
                    
            raise PepperpyError(
                f"Max retry attempts ({max_attempts}) reached for {func.__name__}"
            ) from last_exception
            
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    if attempt > 0:
                        logger.debug(
                            f"Retrying {func.__name__} (attempt {attempt + 1}/{max_attempts})"
                        )
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    continue
                except Exception as e:
                    raise PepperpyError(
                        f"Unhandled error in {func.__name__}: {str(e)}"
                    ) from e
                    
            raise PepperpyError(
                f"Max retry attempts ({max_attempts}) reached for {func.__name__}"
            ) from last_exception
            
        return cast(T, async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper)
        
    return decorator


def timed(name: Optional[str] = None) -> Callable[[T], T]:
    """Timing decorator for performance monitoring.
    
    Args:
        name: Optional name for the timed operation
        
    Returns:
        Decorated function
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            operation = name or func.__name__
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                logger.debug(f"{operation} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error(
                    f"{operation} failed after {duration:.3f}s: {str(e)}"
                )
                raise
                
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            operation = name or func.__name__
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                logger.debug(f"{operation} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error(
                    f"{operation} failed after {duration:.3f}s: {str(e)}"
                )
                raise
                
        return cast(T, async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper)
        
    return decorator


def validate_args(**validators: Callable[[Any], bool]) -> Callable[[T], T]:
    """Argument validation decorator.
    
    Args:
        **validators: Mapping of argument names to validation functions
        
    Returns:
        Decorated function
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate arguments
            for arg_name, validator in validators.items():
                if arg_name in bound_args.arguments:
                    value = bound_args.arguments[arg_name]
                    if not validator(value):
                        raise ValueError(
                            f"Invalid value for argument {arg_name}: {value}"
                        )
                        
            return await func(*args, **kwargs)
            
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate arguments
            for arg_name, validator in validators.items():
                if arg_name in bound_args.arguments:
                    value = bound_args.arguments[arg_name]
                    if not validator(value):
                        raise ValueError(
                            f"Invalid value for argument {arg_name}: {value}"
                        )
                        
            return func(*args, **kwargs)
            
        return cast(T, async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper)
        
    return decorator 