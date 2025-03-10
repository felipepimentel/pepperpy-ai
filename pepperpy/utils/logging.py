"""Logging utilities for PepperPy.

This module provides utilities for configuring and using logging in PepperPy.
"""

import logging
import os
import sys
from typing import Dict, Optional, Union

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}


def configure_logging(
    level: Optional[Union[int, str]] = None,
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """Configure the logging system.

    Args:
        level: The log level (e.g., logging.INFO, "INFO")
        format_string: The log format string
        log_file: The path to the log file
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)

    # Use default level if not specified
    level = level or DEFAULT_LOG_LEVEL

    # Use default format if not specified
    format_string = format_string or DEFAULT_LOG_FORMAT

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: The name of the logger

    Returns:
        The logger
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger

    return _loggers[name]


def set_log_level(level: Union[int, str], logger_name: Optional[str] = None) -> None:
    """Set the log level for a logger.

    Args:
        level: The log level (e.g., logging.INFO, "INFO")
        logger_name: The name of the logger, or None for the root logger
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)

    # Get the logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()

    # Set the level
    logger.setLevel(level)
