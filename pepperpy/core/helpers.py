"""Helper functions for PepperPy core functionality."""

import functools
import importlib
import inspect
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


def import_string(dotted_path: str) -> Any:
    """Import a dotted module path and return the attribute/class.

    Args:
        dotted_path: The dotted path to import

    Returns:
        The imported attribute/class

    Raises:
        ImportError: If the import failed
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as e:
        raise ImportError(f"{dotted_path} doesn't look like a module path") from e

    module = importlib.import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(
            f"Module '{module_path}' does not define a '{class_name}' attribute/class"
        ) from e


def safe_import(module_name: str) -> Optional[Any]:
    """Safely import a module, returning None if it cannot be imported.

    Args:
        module_name: Name of the module to import

    Returns:
        The imported module or None if import failed
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def retry(
    max_tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    hook: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """Function decorator implementing retrying logic.

    Args:
        max_tries: Maximum number of attempts. Default is 3.
        delay: Initial delay between retries in seconds. Default is 1.
        backoff: Backoff multiplier e.g. value of 2 will double the delay. Default is 2.
        exceptions: Tuple of exceptions to catch. Default is (Exception,).
        hook: Function to execute when retry occurs. Default is None.

    Returns:
        A decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tries, delay_val = max_tries, delay
            while tries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    tries -= 1
                    if hook:
                        hook(e, tries)
                    if tries == 1:
                        raise
                    time.sleep(delay_val)
                    delay_val *= backoff
            return func(*args, **kwargs)

        return wrapper

    return decorator


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key
        sep: Separator

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
    """Unflatten a flattened dictionary.

    Args:
        d: Flattened dictionary
        sep: Separator used in keys

    Returns:
        Nested dictionary
    """
    result: Dict[str, Any] = {}
    for key, value in d.items():
        parts = key.split(sep)
        tmp = result
        for part in parts[:-1]:
            if part not in tmp:
                tmp[part] = {}
            tmp = tmp[part]
        tmp[parts[-1]] = value
    return result


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries.

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        Merged configuration dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def convert_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation of the object
    """
    if isinstance(obj, dict):
        return obj
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    elif hasattr(obj, "items"):
        return dict(obj.items())
    else:
        # Try to convert to dict by getting all attributes
        return get_class_attributes(obj)


def get_class_attributes(obj: Any) -> Dict[str, Any]:
    """Get all attributes of a class instance.

    Args:
        obj: Object to inspect

    Returns:
        Dictionary of attributes
    """
    return {
        key: value
        for key, value in inspect.getmembers(obj)
        if not callable(value) and not key.startswith("__")
    }


def format_date(
    dt: Optional[Union[datetime, str]] = None, fmt: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """Format a datetime object or string as a string.

    Args:
        dt: Datetime object or string. Default is current time.
        fmt: Format string. Default is "%Y-%m-%d %H:%M:%S".

    Returns:
        Formatted date string
    """
    if dt is None:
        dt = datetime.now()
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return dt
    return dt.strftime(fmt)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length of the truncated text
        suffix: Suffix to add to truncated text

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def validate_type(value: Any, expected_type: Type[T]) -> T:
    """Validate that a value is of the expected type.

    Args:
        value: Value to validate
        expected_type: Expected type

    Returns:
        The validated value

    Raises:
        TypeError: If the value is not of the expected type
    """
    if not isinstance(value, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, got {type(value).__name__}"
        )
    return value
