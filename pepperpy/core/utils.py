"""Common utility functions used across the PepperPy framework.

This module provides essential utility functions for:
- Type validation
- Text manipulation
- Retry logic
- Dynamic imports
- Class introspection
- Dictionary manipulation
"""

import datetime
import importlib
import inspect
import logging
import time
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from pepperpy.core.types import Metadata

logger = logging.getLogger(__name__)

T = TypeVar("T")


def validate_type(value: Any, expected_type: Type[T], allow_none: bool = False) -> T:
    """Validate that a value matches the expected type.

    Args:
        value: The value to validate
        expected_type: The expected type
        allow_none: Whether to allow None values

    Returns:
        The validated value

    Raises:
        TypeError: If the value is not of the expected type
    """
    if allow_none and value is None:
        return value

    if not isinstance(value, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, got {type(value).__name__}"
        )

    return value


def format_date(
    date: Optional[datetime.datetime] = None,
    format: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Format a date.

    Args:
        date: Optional date to format (defaults to now)
        format: Optional date format string

    Returns:
        Formatted date string
    """
    if date is None:
        date = datetime.datetime.now()
    return date.strftime(format)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add to truncated text

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def retry(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Backoff multiplier
        exceptions: Exceptions to catch

    Returns:
        Result of the function

    Raises:
        Exception: If all attempts fail
    """
    attempt = 0
    last_exception = None

    while attempt < max_attempts:
        try:
            return func()
        except exceptions as e:
            last_exception = e
            attempt += 1
            if attempt >= max_attempts:
                break

            wait_time = delay * (backoff ** (attempt - 1))
            logger.warning(
                f"Attempt {attempt} failed, retrying in {wait_time:.2f}s: {str(e)}"
            )
            time.sleep(wait_time)

    if last_exception:
        raise last_exception
    raise Exception("All retry attempts failed")


def import_string(import_path: str) -> Any:
    """Import a module, class, or function by path.

    Args:
        import_path: Import path (e.g., "module.submodule.ClassName")

    Returns:
        Imported object

    Raises:
        ImportError: If the import fails
    """
    try:
        module_path, name = import_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to import {import_path}: {e}")


def get_class_attributes(cls: Type[Any]) -> Dict[str, Any]:
    """Get all attributes of a class.

    Args:
        cls: Class to get attributes from

    Returns:
        Dictionary of attributes
    """
    return {
        name: value
        for name, value in inspect.getmembers(cls)
        if not name.startswith("__") and not inspect.ismethod(value)
    }


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key for nested values
        sep: Separator for keys

    Returns:
        Flattened dictionary

    Example:
        >>> flatten_dict({"a": {"b": 1, "c": 2}})
        {"a.b": 1, "a.c": 2}
    """
    items = []
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """Unflatten a dictionary with keys containing separators.

    Args:
        d: Dictionary to unflatten
        sep: Separator for keys

    Returns:
        Unflattened dictionary

    Example:
        >>> unflatten_dict({"a.b": 1, "a.c": 2})
        {"a": {"b": 1, "c": 2}}
    """
    result: Dict[str, Any] = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configurations.

    Args:
        *configs: Configurations to merge

    Returns:
        Merged configuration
    """
    result: Dict[str, Any] = {}
    for config in configs:
        for key, value in config.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = merge_configs(result[key], value)
            else:
                result[key] = value
    return result


def safe_import(module_name: str, default: Any = None) -> Any:
    """Safely import a module, returning a default value on failure.

    Args:
        module_name: Name of the module to import
        default: Default value if import fails

    Returns:
        Imported module or default value
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return default


def convert_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation of the object
    """
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        return obj.to_dict()
    elif hasattr(obj, "__dict__"):
        return {
            key: value for key, value in obj.__dict__.items() if not key.startswith("_")
        }
    raise TypeError(f"Cannot convert {type(obj).__name__} to dict")


def get_metadata_value(
    metadata: Optional[Metadata], key: str, default: Any = None
) -> Any:
    """Get a value from metadata using dot notation.

    Args:
        metadata: Metadata dictionary or object
        key: Key to get (supports dot notation for nested values)
        default: Default value if key not found

    Returns:
        Value from metadata or default
    """
    if metadata is None:
        return default

    if not isinstance(metadata, dict):
        metadata = convert_to_dict(metadata)

    if "." not in key:
        return metadata.get(key, default)

    current = metadata
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]

    return current
