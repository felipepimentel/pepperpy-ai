"""Monitoring and observability functionality.

This module provides monitoring and observability tools for the Pepperpy package.
It includes logging, metrics, tracing, and health check functionality.
"""

import logging
import sys
from collections.abc import Mapping
from typing import Any

# Configure root logger
logger = logging.getLogger("pepperpy")
logger.setLevel(logging.INFO)

# Add console handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# Structured logging helper
def log_structured(level: int, message: str, **kwargs: Any) -> None:
    """Log a structured message with additional context.

    Args:
        level: The log level to use
        message: The log message
        **kwargs: Additional context fields
    """
    extra = {k: v if not isinstance(v, Mapping) else dict(v) for k, v in kwargs.items()}
    logger.log(level, message, extra=extra)


# Add convenience methods
def debug(message: str, **kwargs: Any) -> None:
    """Log a debug message."""
    log_structured(logging.DEBUG, message, **kwargs)


def info(message: str, **kwargs: Any) -> None:
    """Log an info message."""
    log_structured(logging.INFO, message, **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    """Log a warning message."""
    log_structured(logging.WARNING, message, **kwargs)


def error(message: str, **kwargs: Any) -> None:
    """Log an error message."""
    log_structured(logging.ERROR, message, **kwargs)


def critical(message: str, **kwargs: Any) -> None:
    """Log a critical message."""
    log_structured(logging.CRITICAL, message, **kwargs)
