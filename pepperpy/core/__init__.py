"""Core functionality for PepperPy.

This module provides core functionality for PepperPy, including:
- Base classes and interfaces
- Configuration handling
- Logging and monitoring
- Memory management
- Type definitions
- Validation
- Dependency injection
- Utility functions
- HTTP client and utilities
- Error handling
- Version information
"""

from .base import (
    BaseProvider,
    PepperpyError,
    ProviderError,
    HTTPError,
    RequestError,
    ResponseError,
    ConnectionError,
    TimeoutError,
    ModelContext,
    BaseModelContext,
)
from .config import Config
from .di import Container
from .logging import Logger, LogLevel, get_logger, setup_logging, VerbosityLevel, configure_logging, get_log_manager
from .memory import BaseMemory, MemoryManager
from .metrics import (
    Metric,
    MetricCategory,
    MetricsCollector,
    PerformanceTracker,
    benchmark,
    get_memory_usage,
    get_system_info,
    measure_memory,
    measure_time,
    performance_tracker,
    report_custom_metric,
)
from .types import Metadata
from .utils import (
    convert_to_dict,
    flatten_dict,
    format_date,
    get_class_attributes,
    get_metadata_value,
    import_string,
    merge_configs,
    retry,
    safe_import,
    truncate_text,
    unflatten_dict,
    validate_type,
    auto_load_env,
)
from .validation import ValidationError, validate_config
from .version import __version__

# Definindo ContextError já que é usado na lista de __all__
class ContextError(PepperpyError):
    """Error raised by context operations."""
    pass

__all__ = [
    # Errors
    "PepperpyError",
    "ProviderError",
    "InvalidOperationError",
    "ValidationError",
    "ConfigError",
    "AuthenticationError",
    "ResourceNotFoundError",
    "NotImplementedError",
    "LimitExceededError",
    # Config
    "Config",
    # Storage
    "StorageConfig",
    "StorageError",
    "ConnectionError",
    "TimeoutError",
    # Types
    "Metadata",
    # Validation
    "validate_config",
    # Utils
    "unflatten_dict",
    "validate_type",
    "auto_load_env",
    # Logging
    "VerbosityLevel",
    "configure_logging",
    "get_logger",
    "get_log_manager",
    # Context
    "BaseModelContext",
    "ContextError",
    # Version
    "__version__",
]
