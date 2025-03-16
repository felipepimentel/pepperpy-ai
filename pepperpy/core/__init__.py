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

# Import from errors.py
from pepperpy.core.errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigError as ConfigurationError,
    NotFoundError as ResourceNotFoundError,
    PepperPyError,
    RateLimitError,
    ValidationError,
)

# Import utility functions from core.py
# TODO[v2.0]: Move these utility functions to a dedicated utils.py file
from pepperpy.core.core import (
    ServiceUnavailableError,
    TimeoutError,
    ensure_dir,
    get_config_dir,
    get_data_dir,
    get_env_var,
    get_logger,
    get_output_dir,
    get_project_root,
)

# Import from public.py
# TODO[v2.0]: Move these to base.py or registry.py
from pepperpy.core.public import (
    ProviderRegistry,
    RegistryError,
    TypeRegistry,
    provider_registry,
    registry_of_registries,
)

# Re-export everything
__all__ = [
    # Core protocols and base classes
    "Analyzer",
    "BaseProvider",
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
]
