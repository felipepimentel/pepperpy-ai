"""Common utility functions used across the PepperPy framework.

This module provides essential utility functions for:
- Type validation and conversion
- Text manipulation and formatting
- Retry logic and error handling
- Dynamic imports and reflection
- Class introspection
- Dictionary manipulation
- Environment variable handling
- Metadata management
"""

import datetime
import importlib
import inspect
import logging
import os
import time
from functools import wraps
from importlib import import_module
from pathlib import Path
from typing import IO, Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from pepperpy.core.types import Metadata

try:
    from dotenv import load_dotenv
except ImportError:
    # Mock load_dotenv if not available
    def load_dotenv(
        dotenv_path: Optional[Union[str, Path]] = None,
        stream: Optional[IO[str]] = None,
        verbose: bool = False,
        override: bool = False,
        **kwargs: Any,
    ) -> bool:
        """Mock function for load_dotenv."""
        print("Warning: python-dotenv not available, skipping environment loading")
        return False


logger = logging.getLogger(__name__)

T = TypeVar("T")


# Import handling
class LazyImportError(ImportError):
    """Raised when a lazy import fails."""

    def __init__(
        self,
        name: str,
        module: str,
        provider: str,
        original_error: Optional[Exception] = None,
    ):
        self.name = name
        self.module = module
        self.provider = provider
        self.original_error = original_error
        message = (
            f"Failed to import '{name}'. This feature requires the '{provider}' provider for the '{module}' module. "
            f"Install it with: pip install pepperpy[{module}-{provider}]"
        )
        if original_error:
            message += f"\nOriginal error: {str(original_error)}"
        super().__init__(message)


def safe_import(module_name: str, package: Optional[str] = None) -> Any:
    """Safely import a module.

    Args:
        module_name: The name of the module to import.
        package: Optional package name for relative imports.

    Returns:
        The imported module.

    Raises:
        ImportError: If the module cannot be imported.
    """
    try:
        return import_module(module_name, package)
    except ImportError as e:
        logger.debug(f"Failed to import {module_name}: {e}")
        raise ImportError(
            f"Failed to import {module_name}. Please install it with: pip install {module_name}"
        ) from e


def lazy_provider_import(module: str, provider: str) -> Callable:
    """Decorator for lazy importing provider-specific dependencies."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except ImportError as e:
                raise LazyImportError(str(e).split("'")[1], module, provider, e)

        return wrapper

    return decorator


def lazy_provider_class(
    provider_name: str,
    provider_type: str,
    required_packages: Optional[Dict[str, str]] = None,
) -> Callable[[Type[T]], Type[T]]:
    """Decorator for lazy loading provider classes."""

    def decorator(cls: Type[T]) -> Type[T]:
        setattr(cls, "_provider_name", provider_name)
        setattr(cls, "_provider_type", provider_type)
        setattr(cls, "_required_packages", required_packages or {})

        original_init = cls.__init__

        @wraps(original_init)
        def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
            for package_name, package_version in getattr(
                cls, "_required_packages"
            ).items():
                try:
                    import_module(package_name)
                except ImportError as e:
                    raise ImportError(
                        f"Failed to import required package {package_name} for {provider_name} {provider_type} provider: {e}"
                    ) from e
            original_init(self, *args, **kwargs)

        cls.__init__ = wrapped_init
        return cls

    return decorator


def import_provider(import_name: str, module: str, provider: str) -> Any:
    """Utility function for provider-specific imports."""
    try:
        return import_module(import_name)
    except ImportError as e:
        raise LazyImportError(import_name, module, provider, e)


def import_string(import_path: str) -> Any:
    """Import a module, class, or function by path."""
    try:
        module_path, name = import_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to import {import_path}: {e}")


# Type validation and conversion
def validate_type(value: Any, expected_type: Type[T], allow_none: bool = False) -> T:
    """Validate that a value matches the expected type."""
    if allow_none and value is None:
        return value

    if not isinstance(value, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, got {type(value).__name__}"
        )

    return value


def convert_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary."""
    if isinstance(obj, dict):
        return obj
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    else:
        return {k: getattr(obj, k) for k in dir(obj) if not k.startswith("_")}


# Text manipulation
def format_date(
    date: Optional[datetime.datetime] = None,
    format: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Format a date."""
    if date is None:
        date = datetime.datetime.now()
    return date.strftime(format)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_number(num: Union[int, float], precision: int = 2) -> str:
    """Format a number with appropriate suffixes."""
    for unit in ["", "K", "M", "B", "T"]:
        if abs(num) < 1000.0:
            return f"{num:3.{precision}f}{unit}"
        num /= 1000.0
    return f"{num:.{precision}f}T"


# Retry logic
def retry(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """Retry a function with exponential backoff."""
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


# Class introspection
def get_class_attributes(cls: Type[Any]) -> Dict[str, Any]:
    """Get all attributes of a class."""
    return {
        name: value
        for name, value in inspect.getmembers(cls)
        if not name.startswith("__") and not inspect.ismethod(value)
    }


def get_class_methods(cls: Type[Any]) -> Dict[str, Any]:
    """Get all methods of a class."""
    return {
        name: value
        for name, value in inspect.getmembers(cls)
        if not name.startswith("__") and inspect.ismethod(value)
    }


def get_method_signature(method: Callable) -> inspect.Signature:
    """Get the signature of a method."""
    return inspect.signature(method)


# Dictionary manipulation
def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items = []
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """Unflatten a dictionary with dot notation keys."""
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return result


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries."""
    result = {}
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


# Environment handling
def auto_load_env(
    env_file: Optional[Union[str, Path]] = None,
    override: bool = False,
    fail_silently: bool = True,
) -> bool:
    """Automatically load environment variables from a .env file."""
    if env_file is None:
        env_file = ".env"

    if isinstance(env_file, str):
        env_file = Path(env_file)

    if not env_file.exists():
        if not fail_silently:
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        return False

    return load_dotenv(dotenv_path=env_file, override=override)


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get a boolean value from an environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "y", "on")


def get_env_int(key: str, default: int = 0) -> int:
    """Get an integer value from an environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get a float value from an environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_env_list(key: str, default: Optional[List[str]] = None) -> List[str]:
    """Get a list value from an environment variable."""
    value = os.getenv(key)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(",")]


# Metadata handling
def get_metadata_value(
    metadata: Optional[Metadata], key: str, default: Any = None
) -> Any:
    """Get a value from metadata with dot notation support."""
    if metadata is None:
        return default

    parts = key.split(".")
    current = metadata
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def set_metadata_value(metadata: Metadata, key: str, value: Any) -> None:
    """Set a value in metadata with dot notation support."""
    parts = key.split(".")
    current = metadata
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def update_metadata(metadata: Metadata, updates: Dict[str, Any]) -> None:
    """Update metadata with new values."""
    for key, value in updates.items():
        set_metadata_value(metadata, key, value)
