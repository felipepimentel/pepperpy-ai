"""
Logging Configuration.

This module provides logging utilities for the PepperPy framework,
including configuration and access to loggers.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Default logging format for console output
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Global logger registry
_loggers: dict[str, logging.Logger] = {}

# Whether logging has been configured
_logging_configured = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    This function returns a logger configured with the PepperPy logging settings.
    If logging has not been configured yet, it will be configured with default settings.

    Args:
        name: Name of the logger, typically the module name

    Returns:
        Configured logger
    """
    # Initialize logging if not already done
    if not _logging_configured:
        configure_logging()

    # Check if logger already exists in registry
    if name in _loggers:
        return _loggers[name]

    # Create and configure new logger
    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger


def configure_logging(
    level: str | int = "INFO",
    log_format: str = DEFAULT_FORMAT,
    log_file: str | None = None,
    console: bool = True,
    max_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """Configure logging for the PepperPy framework.

    Args:
        level: Log level (e.g., "DEBUG", "INFO", "WARNING")
        log_format: Log message format string
        log_file: Optional path to log file
        console: Whether to log to console
        max_size: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
    """
    global _logging_configured

    # Convert string level to logging level
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        level = numeric_level

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if log file specified
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        os.makedirs(log_path.parent, exist_ok=True)

        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Mark logging as configured
    _logging_configured = True

    # Create pepperpy logger and log initialization
    logger = get_logger("pepperpy")
    logger.debug("Logging initialized")


def get_log_level(level_name: str) -> int:
    """Convert log level name to numeric value.

    Args:
        level_name: Log level name (e.g., "DEBUG", "INFO")

    Returns:
        Numeric log level

    Raises:
        ValueError: If log level name is invalid
    """
    level = getattr(logging, level_name.upper(), None)
    if not isinstance(level, int):
        raise ValueError(f"Invalid log level: {level_name}")
    return level


def configure_from_config(config: dict | None = None) -> None:
    """Configure logging from configuration dictionary.

    Args:
        config: Optional logging configuration dictionary
    """
    if not config:
        # Use default configuration
        configure_logging()
        return

    # Extract logging configuration
    level = config.get("level", "INFO")
    log_format = config.get("format", DEFAULT_FORMAT)
    log_file = config.get("file")
    console = config.get("console", True)
    max_size = config.get("max_size", 10 * 1024 * 1024)
    backup_count = config.get("backup_count", 5)

    # Configure logging
    configure_logging(
        level=level,
        log_format=log_format,
        log_file=log_file,
        console=console,
        max_size=max_size,
        backup_count=backup_count,
    )
