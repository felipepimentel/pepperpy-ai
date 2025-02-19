"""Logging module for Pepperpy.

This module provides structured logging utilities.
"""

import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Union

# Configure root logger
logger = logging.getLogger("pepperpy")
logger.setLevel(logging.INFO)

# Add console handler if none exists
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogRecord:
    """Structured log record."""

    message: str
    level: LogLevel
    timestamp: str = field(default_factory=lambda: "")
    context: Dict[str, Any] = field(default_factory=dict)


class StructuredLogger:
    """Structured logger for Pepperpy."""

    def __init__(self, name: str) -> None:
        """Initialize the logger.

        Args:
            name: Logger name
        """
        self._logger = logging.getLogger(name)

    def _log(
        self,
        level: LogLevel,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log a message with the given level.

        Args:
            level: Log level
            message: Log message
            **kwargs: Additional context
        """
        log_level = getattr(logging, level.value)
        self._logger.log(log_level, message, extra=kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: Log message
            **kwargs: Additional context
        """
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            message: Log message
            **kwargs: Additional context
        """
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            message: Log message
            **kwargs: Additional context
        """
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: Log message
            **kwargs: Additional context
        """
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message.

        Args:
            message: Log message
            **kwargs: Additional context
        """
        self._log(LogLevel.CRITICAL, message, **kwargs)


class LoggerFactory:
    """Factory for creating loggers."""

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger by name.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        return logging.getLogger(name)

    @staticmethod
    def get_structured_logger(name: str) -> StructuredLogger:
        """Get a structured logger by name.

        Args:
            name: Logger name

        Returns:
            StructuredLogger instance
        """
        return StructuredLogger(name)


def setup_logging(
    level: Union[LogLevel, str] = LogLevel.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """Set up logging configuration.

    Args:
        level: Log level
        log_file: Optional log file path
        format_string: Optional format string
    """
    if isinstance(level, str):
        level = LogLevel(level.upper())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.value))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Configure format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format_string)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


# Create default structured logger
structured_logger = LoggerFactory.get_structured_logger("pepperpy")

# Expose public interface
__all__ = [
    "LogLevel",
    "LogRecord",
    "LoggerFactory",
    "StructuredLogger",
    "logger",
    "structured_logger",
    "setup_logging",
]
