"""Public API for the PepperPy core module.

This module exports the public API for the PepperPy core module.
It includes core interfaces, base classes, and utilities that are
used throughout the framework.
"""

from pepperpy.core.base import BaseProvider
from pepperpy.core.base_manager import (
    BaseManager,
    ManagerError,
)
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
from pepperpy.core.registry import ProviderRegistry, provider_registry
from pepperpy.registry.base import (
    Registry,
    RegistryError,
    TypeRegistry,
    registry_of_registries,
)
from pepperpy.utils import (
    JSON,
    PathType,
    generate_id,
    generate_timestamp,
    get_file_extension,
    get_file_mime_type,
    get_file_size,
    hash_string,
    is_valid_email,
    is_valid_url,
    load_json,
    retry,
    save_json,
    slugify,
    truncate_string,
)

__all__ = [
    # Core errors
    "PepperPyError",
    "ConfigurationError",
    "ValidationError",
    "ResourceNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "TimeoutError",
    "RateLimitError",
    "ServiceUnavailableError",
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
    # Type definitions
    "JSON",
    "PathType",
    # Utility functions
    "get_logger",
    "generate_id",
    "generate_timestamp",
    "hash_string",
    "load_json",
    "save_json",
    "get_env_var",
    "get_project_root",
    "get_config_dir",
    "get_data_dir",
    "get_output_dir",
    "ensure_dir",
    "slugify",
    "truncate_string",
    "retry",
    "is_valid_email",
    "is_valid_url",
    "get_file_extension",
    "get_file_mime_type",
    "get_file_size",
]
