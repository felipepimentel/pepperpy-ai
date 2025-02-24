"""Logging package for the Pepperpy framework.

This package provides a unified logging system with support for:
- Structured logging with JSON formatting
- Asynchronous logging with file rotation
- Context-based and level-based filtering
- Customizable handlers and formatters
"""

from pepperpy.monitoring.logging.base import (
    LogHandler,
    LogLevel,
    LogManager,
    LogRecord,
)
from pepperpy.monitoring.logging.filters.context import ContextFilter
from pepperpy.monitoring.logging.filters.level import LevelFilter
from pepperpy.monitoring.logging.formatters.json import JsonFormatter
from pepperpy.monitoring.logging.handlers.file import FileHandler

# Export public API
__all__ = [
    "ContextFilter",
    "FileHandler",
    "JsonFormatter",
    "LevelFilter",
    "LogHandler",
    "LogLevel",
    "LogManager",
    "LogRecord",
]
