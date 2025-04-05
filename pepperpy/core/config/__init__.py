"""
PepperPy Configuration System.

This module provides a unified configuration system for PepperPy,
including file loading, schema validation, and access patterns.
"""

# Public exports from manager
# Public exports from loader
from pepperpy.core.config.loader import (
    find_config_file,
    get_env_config,
    load_config,
    merge_configs,
)
from pepperpy.core.config.manager import (
    diagnose_config,
    get_component_config,
    get_config,
    get_default_provider,
    get_environment,
    get_plugin_configuration,
    get_provider_api_key,
    get_provider_config,
    initialize_config,
    is_development,
    is_production,
    validate_config_security,
)

# Public exports from schema
from pepperpy.core.config.schema import (
    EnvVarReference,
    PepperPyConfig,
    Provider,
    SecurityConfig,
)

__all__ = [
    # Manager functions
    "get_config",
    "get_component_config",
    "get_default_provider",
    "get_provider_config",
    "get_provider_api_key",
    "get_plugin_configuration",
    "initialize_config",
    "get_environment",
    "is_development",
    "is_production",
    "diagnose_config",
    "validate_config_security",
    # Schema classes
    "EnvVarReference",
    "PepperPyConfig",
    "Provider",
    "SecurityConfig",
    # Loader functions
    "load_config",
    "find_config_file",
    "merge_configs",
    "get_env_config",
]
