"""Utilities for handling lazy imports."""

from functools import wraps
from importlib import import_module
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast, overload
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")

class LazyImportError(ImportError):
    """Raised when a lazy import fails."""
    
    def __init__(
        self,
        name: str,
        module: str,
        provider: str,
        original_error: Optional[Exception] = None
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
        raise ImportError(f"Failed to import {module_name}. Please install it with: pip install {module_name}") from e

def lazy_provider_import(module: str, provider: str) -> Callable:
    """Decorator for lazy importing provider-specific dependencies.
    
    Args:
        module: The module name (e.g., 'llm', 'rag')
        provider: The provider name (e.g., 'openai', 'chroma')
        
    Returns:
        Decorator function
        
    Example:
        >>> @lazy_provider_import('llm', 'openai')
        ... def use_openai():
        ...     from openai import OpenAI
        ...     client = OpenAI()
        ...     return client
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except ImportError as e:
                raise LazyImportError(
                    str(e).split("'")[1],
                    module,
                    provider,
                    e
                )
        return wrapper
    return decorator

def lazy_provider_class(
    provider_name: str,
    provider_type: str,
    required_packages: Optional[Dict[str, str]] = None,
) -> Callable[[Type[T]], Type[T]]:
    """Decorator for lazy loading provider classes.

    Args:
        provider_name: The name of the provider.
        provider_type: The type of provider (e.g. "llm", "rag", "embeddings").
        required_packages: A dictionary of required packages and their versions.

    Returns:
        A decorator that wraps the provider class.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        """Wrap the provider class with lazy loading."""
        # Store provider information as class attributes
        setattr(cls, "_provider_name", provider_name)
        setattr(cls, "_provider_type", provider_type)
        setattr(cls, "_required_packages", required_packages or {})

        @wraps(cls.__init__)
        def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
            """Wrap the provider class __init__ method."""
            for package_name, package_version in getattr(cls, "_required_packages").items():
                try:
                    import_module(package_name)
                except ImportError as e:
                    raise ImportError(
                        f"Failed to import required package {package_name} for {provider_name} {provider_type} provider: {e}"
                    ) from e

            cls.__init__(self, *args, **kwargs)

        cls.__init__ = wrapped_init
        return cls

    return decorator

def import_provider(import_name: str, module: str, provider: str) -> Any:
    """Utility function for provider-specific imports.
    
    Args:
        import_name: Name of the package to import
        module: The module name (e.g., 'llm', 'rag')
        provider: The provider name (e.g., 'openai', 'chroma')
        
    Returns:
        Imported module
        
    Raises:
        LazyImportError: If import fails
        
    Example:
        >>> openai = import_provider('openai', 'llm', 'openai')
        >>> client = openai.OpenAI()
    """
    try:
        return import_module(import_name)
    except ImportError as e:
        raise LazyImportError(import_name, module, provider, e)

def import_string(import_path: str) -> Any:
    """Import a module or object from a string path.

    Args:
        import_path: The import path (e.g., "pepperpy.core.utils.import_string").

    Returns:
        The imported module or object.

    Raises:
        ImportError: If the module or object cannot be imported.
    """
    try:
        module_path, class_name = import_path.rsplit(".", 1)
    except ValueError as e:
        raise ImportError(f"Invalid import path: {import_path}") from e

    try:
        module = import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Could not import module {module_path}: {e}") from e

    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f"Could not find {class_name} in module {module_path}: {e}") from e 