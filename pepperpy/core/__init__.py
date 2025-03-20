"""Core capabilities for PepperPy.

This module provides core functionality used across the framework,
including configuration, logging, validation, and utilities.

Example:
    >>> from pepperpy.core import Config, Logger, validate_config
    >>> config = Config.from_file("config.yaml")
    >>> logger = Logger.get("my_module")
    >>> validate_config({"api_key": "abc123"}, required=["api_key"])
"""

from pepperpy.core.base import BaseProvider
from pepperpy.core.config import Config, ConfigError
from pepperpy.core.logging import Logger, LogLevel
from pepperpy.core.providers import (
    BaseProvider,
    LocalProvider,
    RemoteProvider,
    RestProvider,
)
from pepperpy.core.utils import (
    flatten_dict,
    get_class_attributes,
    import_string,
    retry,
    truncate_text,
    unflatten_dict,
    validate_type,
)
from pepperpy.core.validation import (
    ValidationError,
    ValidationSchema,
    validate_config,
    validate_pattern,
    validate_range,
)

__all__ = [
    "BaseProvider",
    "Config",
    "ConfigError",
    "LocalProvider",
    "LogLevel",
    "Logger",
    "RemoteProvider",
    "RestProvider",
    "ValidationError",
    "ValidationSchema",
    "flatten_dict",
    "get_class_attributes",
    "import_string",
    "retry",
    "truncate_text",
    "unflatten_dict",
    "validate_config",
    "validate_pattern",
    "validate_range",
    "validate_type",
]
