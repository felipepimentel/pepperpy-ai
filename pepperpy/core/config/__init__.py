"""Configuration management utilities."""

# flake8: noqa
# pylint: disable=line-too-long

import os
import sys
from typing import Any, Dict, List, Optional, Union

# Public exports from loader
from pepperpy.core.config.loader import (
    find_config_file,
    get_env_config,
    load_config,
)

# Public exports from manager
from pepperpy.core.config.manager import (
    ConfigManager,
    diagnose_config,
    get_component_config,
    get_config,
    get_default_provider,
    get_environment,
    get_plugin_configuration,
    get_plugin_config,
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
    SecurityConfig,
    validate_config,
    validate_config_file,
    merge_configs,
    EnvVarResolver,
    ConfigValidator,
)

__all__ = [
    # Manager functions
    "get_config",
    "get_provider_config",
    "get_component_config",
    "get_default_provider",
    "get_provider_api_key",
    "get_plugin_configuration",
    "get_plugin_config",
    "get_environment",
    "is_development",
    "is_production",
    "initialize_config",
    "diagnose_config",
    "validate_config_security",
    "ConfigManager",
    # Schema classes
    "PepperPyConfig",
    "SecurityConfig",
    "EnvVarReference",
    "validate_config",
    "validate_config_file",
    "merge_configs",
    "EnvVarResolver",
    "ConfigValidator",
    # Loader functions
    "load_config",
    "find_config_file",
    "get_env_config",
]
