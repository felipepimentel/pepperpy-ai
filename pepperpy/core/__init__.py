"""Core functionality for PepperPy.

This module provides the core functionality for PepperPy, including:
- Base models and interfaces
- Error handling
- Configuration management
- Validation utilities
- Logging and metrics
- Utility functions
"""

from pepperpy.core.base import (
    BaseComponent,
    BaseProvider,
    Component,
    ComponentError,
    ComponentRegistry,
    ConfigurationError,
    ConnectionError,
    Document,
    GenerationResult,
    HTTPError,
    JsonDict,
    JsonType,
    JsonValue,
    LLMProvider,
    Metadata,
    PepperpyError,
    ProviderError,
    QueryParamsType,
    RAGProvider,
    RequestError,
    ResponseError,
    SearchResult,
    StorageProvider,
    TimeoutError,
    ValidationError,
    WorkflowProvider,
)
from pepperpy.core.config import Config
from pepperpy.core.di import Container
from pepperpy.core.logging import Logger, LogLevel, get_logger
from pepperpy.core.memory import BaseMemory
from pepperpy.core.metrics import MetricsCollector
from pepperpy.core.utils import (
    convert_to_dict,
    flatten_dict,
    format_date,
    get_class_attributes,
    import_string,
    merge_configs,
    retry,
    safe_import,
    truncate_text,
    unflatten_dict,
    validate_type,
)
from pepperpy.core.validation import validate_config
from pepperpy.core.version import __version__

# Re-export error types for convenience
ConfigError = ConfigurationError

__all__ = [
    # Base
    "BaseComponent",
    # Memory
    "BaseMemory",
    "BaseProvider",
    "Component",
    "ComponentError",
    "ComponentRegistry",
    # Config
    "Config",
    "ConfigError",  # Alias for ConfigurationError
    "ConfigurationError",
    # Errors
    "ConnectionError",
    # DI
    "Container",
    # Types
    "Document",
    "GenerationResult",
    "HTTPError",
    "JsonDict",
    "JsonType",
    "JsonValue",
    "LLMProvider",
    "LogLevel",
    # Logging
    "Logger",
    "Metadata",
    # Metrics
    "MetricsCollector",
    "PepperpyError",
    "ProviderError",
    "QueryParamsType",
    "RAGProvider",
    "RequestError",
    "ResponseError",
    "SearchResult",
    "StorageProvider",
    "TimeoutError",
    "ValidationError",
    "WorkflowProvider",
    # Version
    "__version__",
    # Utils
    "convert_to_dict",
    "flatten_dict",
    "format_date",
    "get_class_attributes",
    "get_logger",
    "import_string",
    "merge_configs",
    "retry",
    "safe_import",
    "truncate_text",
    "unflatten_dict",
    # Validation
    "validate_config",
    "validate_type",
]
