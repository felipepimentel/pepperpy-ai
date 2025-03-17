"""PepperPy Core Module.

This module provides the core functionality of the PepperPy framework, including:
- Common types and utilities
- Core interfaces and protocols
- Base classes for providers and processors

The core module is the foundation of the PepperPy framework and is used by
all other modules.
"""

# Import from consolidated base.py file
from pepperpy.core.base import (
    Analyzer,
    BaseManager,
    BaseProvider,
    Cleanable,
    Configurable,
    Generator,
    Identifiable,
    Initializable,
    ManagerError,
    Processor,
    Provider,
    ProviderCapability,
    ProviderConfig,
    Registry,
    Resource,
    ResourceProvider,
    Result,
    Serializable,
    Transformer,
    Validator,
)

# Import from core.py module
from pepperpy.core.core import (
    ServiceUnavailableError,
    TimeoutError,
    ensure_dir,
    get_config_dir,
    get_data_dir,
    get_env_var,
    get_output_dir,
    get_project_root,
)

# Import from errors.py
from pepperpy.core.errors import (
    AuthenticationError,
    AuthorizationError,
    PepperPyError,
    RateLimitError,
    ValidationError,
)
from pepperpy.core.errors import (
    ConfigError as ConfigurationError,
)
from pepperpy.core.errors import (
    NotFoundError as ResourceNotFoundError,
)

# Import from logging.py module
from pepperpy.core.logging import LogLevel, configure_logging, get_logger, set_log_level

# Import from registry module
from pepperpy.core.registry import (
    Registry,
    RegistryError,
    TypeRegistry,
    registry_of_registries,
)

# Import utility types and functions
from pepperpy.utils.base import (
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

# Provider registry (to be defined after importing the required modules)
provider_registry = None
ProviderRegistry = None

__all__ = [
    # Base interfaces and protocols
    "Analyzer",
    "Cleanable",
    "Configurable",
    "Generator",
    "Identifiable",
    "Initializable",
    "Processor",
    "Provider",
    "ProviderCapability",
    "ProviderConfig",
    "Resource",
    "ResourceProvider",
    "Result",
    "Serializable",
    "Transformer",
    "Validator",
    # Error classes
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
    # Type definitions
    "JSON",
    "PathType",
    # Utility functions
    "generate_id",
    "generate_timestamp",
    "hash_string",
    "load_json",
    "save_json",
    "slugify",
    "truncate_string",
    "retry",
    "is_valid_email",
    "is_valid_url",
    "get_file_extension",
    "get_file_mime_type",
    "get_file_size",
    "LogLevel",
    "configure_logging",
    "set_log_level",
]
