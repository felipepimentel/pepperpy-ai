"""PepperPy Core Module.

This module provides the core functionality of the PepperPy framework, including:
- Common types and utilities
- Core interfaces and protocols
- Base classes for providers and processors

The core module is the foundation of the PepperPy framework and is used by
all other modules.
"""

# Import directly from core.py to avoid circular imports
from pepperpy.core.core import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    PepperPyError,
    RateLimitError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    TimeoutError,
    ValidationError,
    ensure_dir,
    get_config_dir,
    get_data_dir,
    get_env_var,
    get_logger,
    get_output_dir,
    get_project_root,
)
from pepperpy.core.public import (
    BaseProvider,
    ProviderRegistry,
    Registry,
    RegistryError,
    TypeRegistry,
    provider_registry,
    registry_of_registries,
    BaseManager,
    ManagerError,
    manager_registry,
)
from pepperpy.errors.core import PepperPyError

# Re-export everything
__all__ = [
    # Errors
    "PepperPyError",
    "ConfigurationError",
    "ValidationError",
    "ResourceNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "TimeoutError",
    "RateLimitError",
    "ServiceUnavailableError",
    # Utility functions
    "get_logger",
    "get_env_var",
    "get_project_root",
    "get_config_dir",
    "get_data_dir",
    "get_output_dir",
    "ensure_dir",
    # Provider classes
    "BaseProvider",
    "ProviderRegistry",
    "provider_registry",
    # Registry classes
    "Registry",
    "TypeRegistry",
    "RegistryError",
    "registry_of_registries",
    # Manager classes
    "BaseManager",
    "ManagerError",
    "manager_registry",
]
