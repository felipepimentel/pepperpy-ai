"""Monitoring package for the Pepperpy framework.

This package provides monitoring functionality including:
- Structured logging with JSON formatting
- Metrics collection and aggregation
- Tracing and profiling
- Health checks and diagnostics
"""

from pepperpy.monitoring.logging import (
    ContextFilter,
    FileHandler,
    JsonFormatter,
    LevelFilter,
    LogLevel,
    LogManager,
    LogRecord,
    get_logger,
)

# Configure base logging
logger = get_logger("pepperpy")

# Export public API
__all__ = [
    # Logging
    "ContextFilter",
    "FileHandler",
    "JsonFormatter",
    "LevelFilter",
    "LogLevel",
    "LogManager",
    "LogRecord",
    "logger",
]