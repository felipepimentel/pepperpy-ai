"""Common utility functions."""

import asyncio
import functools
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from pepperpy.common.errors import PepperpyError


class UtilsError(PepperpyError):
    """Utils error."""
    pass


T = TypeVar("T")


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry decorator for functions.
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        exceptions: Exceptions to catch
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            raise last_error  # type: ignore
        return wrapper
    return decorator


def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry decorator for async functions.
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        exceptions: Exceptions to catch
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
            raise last_error  # type: ignore
        return cast(Callable[..., T], wrapper)
    return decorator


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    """Load JSON file.
    
    Args:
        path: File path
        
    Returns:
        Loaded JSON data
        
    Raises:
        UtilsError: If loading fails
    """
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        raise UtilsError(f"Failed to load JSON file: {str(e)}")


def save_json(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """Save JSON file.
    
    Args:
        data: Data to save
        path: File path
        
    Raises:
        UtilsError: If saving fails
    """
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise UtilsError(f"Failed to save JSON file: {str(e)}")


def ensure_dir(path: Union[str, Path]) -> None:
    """Ensure directory exists.
    
    Args:
        path: Directory path
        
    Raises:
        UtilsError: If directory creation fails
    """
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        raise UtilsError(f"Failed to create directory: {str(e)}")


def get_env(key: str, default: Optional[str] = None) -> str:
    """Get environment variable.
    
    Args:
        key: Environment variable key
        default: Optional default value
        
    Returns:
        Environment variable value
        
    Raises:
        UtilsError: If variable not found and no default
    """
    value = os.getenv(key, default)
    if value is None:
        raise UtilsError(f"Environment variable not found: {key}")
    return value


__all__ = [
    "UtilsError",
    "retry",
    "async_retry",
    "load_json",
    "save_json",
    "ensure_dir",
    "get_env",
] 