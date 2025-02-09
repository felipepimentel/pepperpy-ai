"""Monitoring and observability functionality.

This module provides monitoring and observability tools for the Pepperpy package.
It includes logging, metrics, tracing, and health check functionality.
"""

import logging
import sys
from pathlib import Path

from pepperpy.monitoring.logger import logger as pepperpy_logger

# Configure root logger
root_logger = logging.getLogger("pepperpy")
root_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Add console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
console_handler.setFormatter(console_formatter)
root_logger.addHandler(console_handler)

# Add file handler
file_handler = logging.FileHandler(logs_dir / "pepperpy.log")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
file_handler.setFormatter(file_formatter)
root_logger.addHandler(file_handler)

# Configure metrics
metrics_enabled = True
metrics_port = 8000

# Configure tracing
tracing_enabled = True
tracing_port = 8001

# Export configuration
__all__ = [
    "metrics_enabled",
    "metrics_port",
    "pepperpy_logger",
    "root_logger",
    "tracing_enabled",
    "tracing_port",
]

LogContext = dict[str, str | int | float | bool | None]


# Structured logging helper
def log_structured(level: int, message: str, **kwargs: LogContext) -> None:
    """Log a structured message with additional context.

    Args:
        level: Log level.
        message: Log message.
        **kwargs: Additional context values.
    """
    root_logger.opt(depth=1).log(level, message, **kwargs)


# Add convenience methods
def debug(message: str, **kwargs: LogContext) -> None:
    """Log a debug message."""
    log_structured(logging.DEBUG, message, **kwargs)


def info(message: str, **kwargs: LogContext) -> None:
    """Log an info message."""
    log_structured(logging.INFO, message, **kwargs)


def warning(message: str, **kwargs: LogContext) -> None:
    """Log a warning message."""
    log_structured(logging.WARNING, message, **kwargs)


def error(message: str, **kwargs: LogContext) -> None:
    """Log an error message."""
    log_structured(logging.ERROR, message, **kwargs)


def critical(message: str, **kwargs: LogContext) -> None:
    """Log a critical message."""
    log_structured(logging.CRITICAL, message, **kwargs)
