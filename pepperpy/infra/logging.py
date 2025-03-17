"""Logging utilities for PepperPy.

This module provides logging utilities for the PepperPy framework.
It includes functions for configuring logging, getting loggers, and setting log levels.

Typical usage:
    from pepperpy.infra.logging import configure_logging, get_logger

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
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Union

from pepperpy.infra.config import get_config


class LogLevel(Enum):
    """Log levels for the PepperPy framework.

    This enum maps standard logging levels to human-readable names.
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def from_string(cls, level_name: str) -> "LogLevel":
        """Convert a string level name to a LogLevel.

        Args:
            level_name: The level name as a string

        Returns:
            The corresponding LogLevel

        Raises:
            ValueError: If the level name is not valid
        """
        try:
            return cls[level_name.upper()]
        except KeyError:
            raise ValueError(f"Invalid log level: {level_name}")

    @classmethod
    def to_int(cls, level: Union[str, int, "LogLevel"]) -> int:
        """Convert a level to its integer value.

        Args:
            level: The level as a string, integer, or LogLevel

        Returns:
            The integer value of the level
        """
        if isinstance(level, cls):
            return level.value
        elif isinstance(level, str):
            return cls.from_string(level).value
        elif isinstance(level, int):
            return level
        else:
            raise ValueError(f"Invalid log level type: {type(level)}")


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
    # Try to get configuration from config if available
    try:
        config = get_config("logging")
        config_dict = config.to_dict()
        if level is None and "level" in config_dict:
            level = config_dict["level"]
        if format_string is None and "format" in config_dict:
            format_string = config_dict["format"]
        if log_file is None and "file" in config_dict:
            log_file = config_dict["file"]
    except Exception:
        # If config is not available, use defaults
        pass

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


def initialize_logging() -> None:
    """Initialize logging from configuration.

    This function initializes logging using the configuration from the config module.
    It should be called once at the start of your application.
    """
    try:
        config = get_config("logging")
        config_dict = config.to_dict()

        configure_logging(
            level=config_dict.get("level"),
            format_string=config_dict.get("format"),
            log_file=config_dict.get("file"),
        )
    except Exception as e:
        # If config is not available, use defaults
        configure_logging()
        logger = get_logger(__name__)
        logger.warning(f"Failed to initialize logging from config: {e}")
