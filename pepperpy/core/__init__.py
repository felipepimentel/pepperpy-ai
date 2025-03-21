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
"""

from .base import BaseProvider
from .config import Config
from .di import Container
from .http import (
    ConnectionError,
    HTTPClient,
    HTTPError,
    HTTPResponse,
    RequestError,
    ResponseError,
    TimeoutError,
    check_status_code,
    format_headers,
    get_content_type,
    is_json_content,
    parse_json,
    parse_query_params,
)
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

__all__ = [
    # Base
    "BaseProvider",
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
    "HTTPClient",
    "HTTPResponse",
    "HTTPError",
    "RequestError",
    "ResponseError",
    "ConnectionError",
    "TimeoutError",
    "check_status_code",
    "format_headers",
    "get_content_type",
    "is_json_content",
    "parse_json",
    "parse_query_params",
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
