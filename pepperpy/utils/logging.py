"""Logging utilities for PepperPy.

This module provides logging utilities for the PepperPy framework.
It includes functions for configuring logging, getting loggers, and setting log levels.

Typical usage:
    from pepperpy.utils.logging import configure_logging, get_logger

    # Configure logging once at the start of your application
    configure_logging(level="INFO", log_file="app.log")

    # Get a logger for your module
    logger = get_logger(__name__)

    # Use the logger
    logger.info("This is an info message")
    logger.error("This is an error message")
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Union

# Cache of loggers
_loggers: Dict[str, logging.Logger] = {}

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging(
    level: Optional[Union[int, str]] = None,
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True,
) -> None:
    """Configure the logging system.

    This should be called once at the start of your application.

    Args:
        level: The log level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        format_string: The format string for log messages
        log_file: The path to the log file
        console: Whether to log to the console
    """
    # Convert string level to int if needed
    numeric_level: int
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
    elif level is None:
        numeric_level = logging.INFO
    else:
        numeric_level = level

    # Use default format if none is provided
    if format_string is None:
        format_string = DEFAULT_FORMAT

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if a log file is specified
    if log_file:
        # Ensure the directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)

        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    This function caches loggers to avoid creating duplicates,
    which ensures that the same logger is returned for the same name.

    Args:
        name: The name of the logger, typically __name__

    Returns:
        The logger
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger

    return _loggers[name]


def set_log_level(level: Union[int, str], logger_name: Optional[str] = None) -> None:
    """Set the log level for a logger or the root logger.

    Args:
        level: The log level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        logger_name: The name of the logger, or None for the root logger
    """
    # Convert string level to int if needed
    numeric_level: int
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
    else:
        numeric_level = level

    # Get the logger
    if logger_name is None:
        logger = logging.getLogger()
    else:
        logger = get_logger(logger_name)

    # Set the level
    logger.setLevel(numeric_level)
