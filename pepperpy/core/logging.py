"""
PepperPy Logging System.

This module provides logging utilities for the PepperPy framework,
including configuration, context, and helper functions.
"""

import logging
import os
import sys
from typing import Optional

# Configure default logging format
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_LOG_LEVEL = "INFO"


def configure_logging(
    level: Optional[str] = None,
    format_str: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """Configure the logging system.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: Log format string
        log_file: File to write logs to
    """
    log_level = level or os.environ.get("PEPPERPY_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    log_format = format_str or LOG_FORMAT

    # Configure root logger
    logging.basicConfig(
        level=logging.getLevelName(log_level.upper()),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            *([logging.FileHandler(log_file)] if log_file else []),
        ],
    )

    # Silence some noisy loggers
    for logger_name in ["urllib3", "httpx"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Args:
        name: Module name or logger name

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
