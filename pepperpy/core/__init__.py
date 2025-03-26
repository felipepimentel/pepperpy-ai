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
    BaseProvider,
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

__all__ = [
    # Base
    "BaseProvider",
    # Config
    "Config",
    # DI
    "Container",
    # Errors
    "ConfigurationError",
    "ConnectionError",
    "HTTPError",
    "PepperpyError",
    "ProviderError",
    "RequestError",
    "ResponseError",
    "TimeoutError",
    "ValidationError",
    # Logging
    "Logger",
    "LogLevel",
    "get_logger",
    # Memory
    "BaseMemory",
    # Metrics
    "MetricsCollector",
    # Types
    "Document",
    "GenerationResult",
    "JsonDict",
    "JsonType",
    "JsonValue",
    "LLMProvider",
    "Metadata",
    "QueryParamsType",
    "RAGProvider",
    "SearchResult",
    "StorageProvider",
    "WorkflowProvider",
    # Utils
    "convert_to_dict",
    "flatten_dict",
    "format_date",
    "get_class_attributes",
    "import_string",
    "merge_configs",
    "retry",
    "safe_import",
    "truncate_text",
    "unflatten_dict",
    "validate_type",
    # Validation
    "validate_config",
    # Version
    "__version__",
]
