"""Utilities Module.

This module provides common utility functions used across the PepperPy
framework. It includes functions for type checking, data validation,
string manipulation, and other general-purpose operations.

Example:
    >>> from pepperpy.core.utils import validate_type, truncate_text
    >>> validate_type("test", str, "name")  # No error
    >>> truncate_text("Long text...", max_length=10)  # "Long tex..."
"""

import importlib
import inspect
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Type, TypeVar, Union, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")


def validate_type(value: Any, expected_type: Type[T], param_name: str) -> T:
    """Validate that a value is of the expected type.

    Args:
        value: The value to validate
        expected_type: The expected type
        param_name: Name of the parameter (for error messages)

    Returns:
        The validated value

    Raises:
        TypeError: If value is not of expected_type

    Example:
        >>> value = validate_type("test", str, "name")
        >>> assert isinstance(value, str)
        >>> validate_type(123, str, "name")  # Raises TypeError
    """
    if not isinstance(value, expected_type):
        raise TypeError(
            f"Parameter '{param_name}' must be of type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
    return value


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: String to append when truncating

    Returns:
        Truncated text

    Example:
        >>> text = "This is a very long text that needs truncating"
        >>> truncate_text(text, max_length=20)
        'This is a very lon...'
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def retry(
    max_attempts: int = 3,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
    delay: float = 0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        exceptions: Exception(s) to catch and retry on
        delay: Delay between retries in seconds

    Returns:
        Decorated function

    Example:
        >>> @retry(max_attempts=3, exceptions=ValueError)
        ... def unstable_function():
        ...     if random.random() < 0.5:
        ...         raise ValueError("Random failure")
        ...     return "success"
    """
    import time

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}",
                            extra={"data": {"function": func.__name__}},
                        )
                        if delay:
                            time.sleep(delay)
                    continue
            if last_exception:
                raise last_exception
            return cast(T, None)  # Should never reach here

        return wrapper

    return decorator


def import_string(import_name: str) -> Any:
    """Import an object based on a string.

    This function imports a module or object using a string path.
    It supports both module imports and attribute access.

    Args:
        import_name: Dotted path to the object

    Returns:
        The imported object

    Raises:
        ImportError: If the object cannot be imported

    Example:
        >>> json = import_string("json")
        >>> dumps = import_string("json.dumps")
        >>> assert callable(dumps)
    """
    module_name, obj_name = (
        import_name.rsplit(".", 1) if "." in import_name else (import_name, None)
    )
    try:
        module = importlib.import_module(module_name)
        if obj_name:
            try:
                return getattr(module, obj_name)
            except AttributeError as e:
                raise ImportError(
                    f"Module '{module_name}' has no attribute '{obj_name}'"
                ) from e
        return module
    except ImportError as e:
        raise ImportError(f"Could not import '{import_name}': {e}") from e


def get_class_attributes(cls: Type[Any]) -> Dict[str, Any]:
    """Get all attributes of a class.

    This function returns a dictionary of all attributes defined in a class,
    including properties and methods, but excluding built-in attributes.

    Args:
        cls: The class to inspect

    Returns:
        Dictionary of attribute names and values

    Example:
        >>> class Example:
        ...     x = 1
        ...     def method(self): pass
        ...     @property
        ...     def prop(self): return 2
        >>> attrs = get_class_attributes(Example)
        >>> assert "x" in attrs and "method" in attrs
    """
    return {
        name: value
        for name, value in inspect.getmembers(cls)
        if not name.startswith("_")
        and not inspect.isbuiltin(value)
        and not inspect.ismodule(value)
    }


def flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
) -> Dict[str, Any]:
    """Flatten a nested dictionary.

    This function converts a nested dictionary into a flat dictionary
    with keys joined by a separator.

    Args:
        d: Dictionary to flatten
        parent_key: Key of parent dictionary (used in recursion)
        sep: Separator for nested keys

    Returns:
        Flattened dictionary

    Example:
        >>> d = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
        >>> flat = flatten_dict(d)
        >>> assert flat == {"a": 1, "b.c": 2, "b.d.e": 3}
    """
    items: List[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """Convert a flattened dictionary back to nested form.

    This function is the inverse of flatten_dict, converting a flat
    dictionary with separated keys back into a nested dictionary.

    Args:
        d: Flattened dictionary
        sep: Separator used in keys

    Returns:
        Nested dictionary

    Example:
        >>> flat = {"a": 1, "b.c": 2, "b.d.e": 3}
        >>> nested = unflatten_dict(flat)
        >>> assert nested == {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
    """
    result: Dict[str, Any] = {}
    for key, value in d.items():
        parts = key.split(sep)
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return result


__all__ = [
    "validate_type",
    "truncate_text",
    "retry",
    "import_string",
    "get_class_attributes",
    "flatten_dict",
    "unflatten_dict",
]
