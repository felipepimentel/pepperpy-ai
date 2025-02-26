"""Logging package for the Pepperpy framework.

This package provides a unified logging system with support for:
- Structured logging with JSON formatting
- Asynchronous logging with file rotation
- Context-based and level-based filtering
- Customizable handlers and formatters
"""

import logging

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


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger


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
    "get_logger",
]
