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
)
from .config import Config
from .di import Container
from .logging import Logger, LogLevel, get_logger, setup_logging
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
)
from .validation import ValidationError, validate_config
from .version import __version__

__all__ = [
    # Version
    "__version__",
    # Base
    "BaseProvider",
    # Errors
    "PepperpyError",
    "ProviderError",
    # Config
    "Config",
    # DI
    "Container",
    # Logging
    "Logger",
    "LogLevel",
    "get_logger",
    "setup_logging",
    # Memory
    "BaseMemory",
    "MemoryManager",
    # Metrics
    "Metric",
    "MetricCategory",
    "MetricsCollector",
    "PerformanceTracker",
    "benchmark",
    "get_memory_usage",
    "get_system_info",
    "measure_memory",
    "measure_time",
    "performance_tracker",
    "report_custom_metric",
    # HTTP
    "HTTPError",
    "RequestError",
    "ResponseError",
    "ConnectionError",
    "TimeoutError",
    # Types
    "Metadata",
    # Validation
    "ValidationError",
    "validate_config",
    # Utils
    "convert_to_dict",
    "flatten_dict",
    "format_date",
    "get_class_attributes",
    "get_metadata_value",
    "import_string",
    "merge_configs",
    "retry",
    "safe_import",
    "truncate_text",
    "unflatten_dict",
    "validate_type",
]
