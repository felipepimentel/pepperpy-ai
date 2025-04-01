"""Helper functions for PepperPy.

This module provides utility functions used throughout the framework.
"""

import functools
import importlib
import logging
import time
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from pepperpy.core.errors import ConfigurationError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def lazy_provider_class(provider_path: str) -> Type[Any]:
    """Lazily import a provider class.

    Args:
        provider_path: Dotted path to provider class

    Returns:
        Provider class

    Raises:
        ConfigurationError: If provider cannot be imported
    """
    try:
        module_path, class_name = provider_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ConfigurationError(
            f"Failed to import provider {provider_path}: {e}"
        ) from e


def import_provider(provider_path: str) -> Any:
    """Import a provider module or class.

    Args:
        provider_path: Dotted path to provider

    Returns:
        Imported provider

    Raises:
        ConfigurationError: If provider cannot be imported
    """
    try:
        return importlib.import_module(provider_path)
    except ImportError:
        try:
            return lazy_provider_class(provider_path)
        except Exception as e2:
            raise ConfigurationError(
                f"Failed to import provider {provider_path}: {e2}"
            ) from e2


def retry(
    max_tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    hook: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """Retry decorator with exponential backoff.

    Args:
        max_tries: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
        hook: Optional callback for retry events

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _delay = delay
            last_exception = None

            for n in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if n == max_tries - 1:
                        raise

                    if hook:
                        hook(e, n)

                    time.sleep(_delay)
                    _delay *= backoff

            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


def format_string(template: str, **kwargs: Any) -> str:
    """Format a string template with keyword arguments.

    Args:
        template: String template
        **kwargs: Format arguments

    Returns:
        Formatted string

    Raises:
        ValueError: If required arguments are missing
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required argument {e} for template: {template}")


def convert_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation
    """
    return getattr(obj, "__dict__", {})


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator between keys

    Returns:
        Flattened dictionary
    """
    items: list = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """Unflatten a dictionary with dotted keys.

    Args:
        d: Dictionary to unflatten
        sep: Key separator

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
