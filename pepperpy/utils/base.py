"""Common utility functions used across the PepperPy framework.

This module provides essential utility functions for:
- Type validation
- Text manipulation
- Retry logic
- Dynamic imports
- Class introspection
- Dictionary manipulation
"""

import importlib
import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

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


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: The text to truncate
        max_length: Maximum length of the text
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


def retry(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """Retry a function with exponential backoff.

    Args:
        func: The function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch

    Returns:
        The result of the function

    Raises:
        Exception: If all attempts fail
    """
    attempt = 0
    current_delay = delay

    while attempt < max_attempts:
        try:
            return func()
        except exceptions as e:
            attempt += 1
            if attempt == max_attempts:
                raise
            logger.warning(
                f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s..."
            )
            time.sleep(current_delay)
            current_delay *= backoff


def import_string(import_path: str) -> Any:
    """Import an object from a string path.

    Args:
        import_path: The import path (e.g. 'module.submodule:object')

    Returns:
        The imported object

    Raises:
        ImportError: If the import fails
    """
    try:
        module_path, object_name = import_path.split(":")
        module = importlib.import_module(module_path)
        return getattr(module, object_name)
    except (ValueError, ImportError, AttributeError) as e:
        raise ImportError(f"Failed to import {import_path}: {e}")


def get_class_attributes(cls: Type[Any]) -> Dict[str, Any]:
    """Get all attributes of a class.

    Args:
        cls: The class to inspect

    Returns:
        Dictionary of attribute names and values
    """
    return {
        name: value
        for name, value in inspect.getmembers(cls)
        if not name.startswith("_")
    }


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: The dictionary to flatten
        parent_key: The parent key for nested items
        sep: The separator between keys

    Returns:
        Flattened dictionary
    """
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """Unflatten a dictionary with dot notation.

    Args:
        d: The dictionary to unflatten
        sep: The separator between keys

    Returns:
        Unflattened dictionary
    """
    result: Dict[str, Any] = {}
    for key, value in d.items():
        parts = key.split(sep)
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return result


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries.

    Args:
        *configs: Configuration dictionaries to merge

    Returns:
        Merged configuration dictionary
    """
    result: Dict[str, Any] = {}
    for config in configs:
        result.update(config)
    return result


def safe_import(module_name: str, default: Any = None) -> Any:
    """Safely import a module or return a default value.

    Args:
        module_name: The module to import
        default: Default value if import fails

    Returns:
        The imported module or default value
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return default


def convert_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary.

    Args:
        obj: The object to convert

    Returns:
        Dictionary representation of the object
    """
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return {}


def get_metadata_value(
    metadata: Optional[Metadata], key: str, default: Any = None
) -> Any:
    """Get a value from metadata with a default fallback.

    Args:
        metadata: The metadata dictionary
        key: The key to look up
        default: Default value if key not found

    Returns:
        The metadata value or default
    """
    if not metadata:
        return default
    return metadata.get(key, default)
