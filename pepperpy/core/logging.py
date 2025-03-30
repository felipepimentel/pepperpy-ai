"""Logging utilities for PepperPy.

This module provides logging utilities for PepperPy, replacing the need for
third-party logging libraries in plugins.
"""

import logging
import os
import sys
from typing import Dict, Optional, Union

# Configure default logger
LOGGER_FORMAT = "%(levelname)s - %(name)s - %(message)s"
DEFAULT_LEVEL = logging.INFO

# Environment variable for log level
LOG_LEVEL_ENV = "PEPPERPY_LOG_LEVEL"

# Configure root logger
logging.basicConfig(
    level=getattr(logging, os.getenv(LOG_LEVEL_ENV, "INFO").upper(), logging.INFO),
    format=LOGGER_FORMAT,
    stream=sys.stdout,
)

# Store loggers to avoid recreation
_loggers: Dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger


def set_log_level(level: Union[str, int]) -> None:
    """Set the log level for all PepperPy loggers.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or logging level constant
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    for logger in _loggers.values():
        logger.setLevel(level)


def debug(msg: str, *args, **kwargs) -> None:
    """Log a debug message from the caller's module.

    Args:
        msg: Debug message
        *args: Arguments for string formatting
        **kwargs: Keyword arguments for string formatting
    """
    caller_frame = sys._getframe(1)
    module = caller_frame.f_globals.get("__name__", "unknown")
    get_logger(module).debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """Log an info message from the caller's module.

    Args:
        msg: Info message
        *args: Arguments for string formatting
        **kwargs: Keyword arguments for string formatting
    """
    caller_frame = sys._getframe(1)
    module = caller_frame.f_globals.get("__name__", "unknown")
    get_logger(module).info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """Log a warning message from the caller's module.

    Args:
        msg: Warning message
        *args: Arguments for string formatting
        **kwargs: Keyword arguments for string formatting
    """
    caller_frame = sys._getframe(1)
    module = caller_frame.f_globals.get("__name__", "unknown")
    get_logger(module).warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """Log an error message from the caller's module.

    Args:
        msg: Error message
        *args: Arguments for string formatting
        **kwargs: Keyword arguments for string formatting
    """
    caller_frame = sys._getframe(1)
    module = caller_frame.f_globals.get("__name__", "unknown")
    get_logger(module).error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    """Log a critical message from the caller's module.

    Args:
        msg: Critical message
        *args: Arguments for string formatting
        **kwargs: Keyword arguments for string formatting
    """
    caller_frame = sys._getframe(1)
    module = caller_frame.f_globals.get("__name__", "unknown")
    get_logger(module).critical(msg, *args, **kwargs)


def add_file_handler(
    filename: str,
    level: Optional[Union[str, int]] = None,
    formatter: Optional[str] = None,
) -> None:
    """Add a file handler to the root logger.

    Args:
        filename: Log file name
        level: Log level (defaults to root logger level)
        formatter: Log format (defaults to LOGGER_FORMAT)
    """
    log_level: int
    if isinstance(level, str):
        log_level = getattr(logging, level.upper(), logging.INFO)
    elif level is None:
        log_level = logging.getLogger().level
    else:
        # Ensure level is a valid logging level
        log_level = int(level)

    handler = logging.FileHandler(filename)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(formatter or LOGGER_FORMAT))
    logging.getLogger().addHandler(handler)


# Provide aliases for compatibility with loguru-style imports
class LoggingFunctions:
    """Class providing function aliases for compatibility with loguru-style imports."""

    @staticmethod
    def debug(msg: str, *args, **kwargs) -> None:
        """Alias for debug()."""
        debug(msg, *args, **kwargs)

    @staticmethod
    def info(msg: str, *args, **kwargs) -> None:
        """Alias for info()."""
        info(msg, *args, **kwargs)

    @staticmethod
    def warning(msg: str, *args, **kwargs) -> None:
        """Alias for warning()."""
        warning(msg, *args, **kwargs)

    @staticmethod
    def error(msg: str, *args, **kwargs) -> None:
        """Alias for error()."""
        error(msg, *args, **kwargs)

    @staticmethod
    def critical(msg: str, *args, **kwargs) -> None:
        """Alias for critical()."""
        critical(msg, *args, **kwargs)


# Create a logger instance that can be used like loguru.logger
logger = LoggingFunctions()
