"""Logging Module.

This module provides structured logging with context management and
formatting options. It supports different log levels, handlers, and
output formats.

Example:
    >>> from pepperpy.core.logging import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing request", request_id="123")
"""

import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from .validation import ValidationError


class LogLevel(Enum):
    """Log levels for message severity.

    This enum defines standard log levels used throughout the system.
    Each level has an associated integer value for comparison.

    Example:
        >>> level = LogLevel.INFO
        >>> if level >= LogLevel.DEBUG:
        ...     print("Debug logging enabled")
    """

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    def __ge__(self, other: "LogLevel") -> bool:
        """Compare log levels.

        Args:
            other: Level to compare against

        Returns:
            True if this level is >= other
        """
        return self.value >= other.value


class LogRecord:
    """Log record with context and metadata.

    This class represents a single log message with associated context,
    timestamp, and metadata.

    Args:
        level: Log level
        message: Log message
        context: Optional context dictionary
        **kwargs: Additional metadata

    Example:
        >>> record = LogRecord(
        ...     LogLevel.INFO,
        ...     "Request processed",
        ...     context={"request_id": "123"},
        ...     duration_ms=42
        ... )
    """

    def __init__(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Initialize log record.

        Args:
            level: Log level
            message: Log message
            context: Optional context dictionary
            **kwargs: Additional metadata
        """
        self.level = level
        self.message = message
        self.context = context or {}
        self.metadata = kwargs
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary.

        Returns:
            Dictionary representation of record

        Example:
            >>> record = LogRecord(LogLevel.INFO, "Test")
            >>> data = record.to_dict()
            >>> print(data["level"])  # "INFO"
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "message": self.message,
            "context": self.context,
            **self.metadata,
        }

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            String representation of record

        Example:
            >>> record = LogRecord(LogLevel.INFO, "Test")
            >>> str(record)  # Contains timestamp and message
        """
        return f"[{self.timestamp.isoformat()}] {self.level.name}: {self.message}"


class Logger:
    """Structured logger with context.

    This class provides structured logging with support for context
    management, multiple handlers, and different output formats.

    Args:
        name: Logger name
        level: Minimum log level
        handlers: Optional list of handlers
        **kwargs: Additional logger options

    Example:
        >>> logger = Logger("app")
        >>> with logger.context(request_id="123"):
        ...     logger.info("Processing request")
    """

    def __init__(
        self,
        name: str,
        level: Union[LogLevel, str] = LogLevel.INFO,
        handlers: Optional[list[logging.Handler]] = None,
        **kwargs: Any,
    ):
        """Initialize logger.

        Args:
            name: Logger name
            level: Minimum log level
            handlers: Optional list of handlers
            **kwargs: Additional logger options

        Raises:
            ValidationError: If name is empty or handlers invalid
        """
        if not name:
            raise ValidationError("Logger name cannot be empty")

        self.name = name
        self.level = level if isinstance(level, LogLevel) else LogLevel[level.upper()]
        self._context: Dict[str, Any] = {}
        self._handlers = handlers or [logging.StreamHandler(sys.stdout)]
        self._options = kwargs

        # Configure handlers
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        for handler in self._handlers:
            handler.setFormatter(formatter)

    @classmethod
    def get_logger(
        cls,
        name: str,
        **kwargs: Any,
    ) -> "Logger":
        """Get logger instance.

        Args:
            name: Logger name
            **kwargs: Additional logger options

        Returns:
            Logger instance

        Example:
            >>> logger = Logger.get_logger(__name__)
            >>> logger.info("Application started")
        """
        return cls(name, **kwargs)

    def set_level(self, level: Union[LogLevel, str]) -> None:
        """Set minimum log level.

        Args:
            level: New log level

        Example:
            >>> logger.set_level(LogLevel.DEBUG)
            >>> logger.set_level("INFO")
        """
        self.level = level if isinstance(level, LogLevel) else LogLevel[level.upper()]

    def add_handler(self, handler: logging.Handler) -> None:
        """Add log handler.

        Args:
            handler: Handler to add

        Example:
            >>> file_handler = logging.FileHandler("app.log")
            >>> logger.add_handler(file_handler)
        """
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        self._handlers.append(handler)

    def context(self, **kwargs: Any) -> "LoggerContext":
        """Create context manager.

        Args:
            **kwargs: Context key-value pairs

        Returns:
            Context manager

        Example:
            >>> with logger.context(request_id="123"):
            ...     logger.info("Processing request")
        """
        return LoggerContext(self, kwargs)

    def log(
        self,
        level: LogLevel,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log message with level.

        Args:
            level: Log level
            message: Log message
            **kwargs: Additional metadata

        Example:
            >>> logger.log(LogLevel.INFO, "Test", user_id="123")
        """
        if level.value < self.level.value:
            return

        record = LogRecord(
            level,
            message,
            context=dict(self._context),
            **kwargs,
        )

        for handler in self._handlers:
            handler.handle(
                logging.LogRecord(
                    name=self.name,
                    level=level.value,
                    pathname="",
                    lineno=0,
                    msg=str(record),
                    args=(),
                    exc_info=None,
                )
            )

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message.

        Args:
            message: Log message
            **kwargs: Additional metadata

        Example:
            >>> logger.debug("Processing item", item_id="123")
        """
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message.

        Args:
            message: Log message
            **kwargs: Additional metadata

        Example:
            >>> logger.info("Request completed", duration_ms=42)
        """
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message.

        Args:
            message: Log message
            **kwargs: Additional metadata

        Example:
            >>> logger.warning("Resource not found", path="/test")
        """
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message.

        Args:
            message: Log message
            **kwargs: Additional metadata

        Example:
            >>> logger.error("Operation failed", error="Connection refused")
        """
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message.

        Args:
            message: Log message
            **kwargs: Additional metadata

        Example:
            >>> logger.critical("System shutdown", reason="Out of memory")
        """
        self.log(LogLevel.CRITICAL, message, **kwargs)


class LoggerContext:
    """Context manager for logger.

    This class provides a context manager that temporarily adds context
    to log messages.

    Args:
        logger: Logger instance
        context: Context dictionary

    Example:
        >>> with LoggerContext(logger, {"request_id": "123"}):
        ...     logger.info("Processing request")
    """

    def __init__(
        self,
        logger: Logger,
        context: Dict[str, Any],
    ):
        """Initialize logger context.

        Args:
            logger: Logger instance
            context: Context dictionary
        """
        self.logger = logger
        self.context = context
        self.previous: Dict[str, Any] = {}

    def __enter__(self) -> None:
        """Enter context manager.

        This method saves the previous context and updates with new values.
        """
        self.previous = dict(self.logger._context)
        self.logger._context.update(self.context)

    def __exit__(self, *args: Any) -> None:
        """Exit context manager.

        This method restores the previous context.
        """
        self.logger._context = self.previous


def setup_logging(
    level: Optional[int] = None,
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """Set up logging configuration.

    Args:
        level: Log level (defaults to INFO)
        format: Log message format
    """
    if level is None:
        level = logging.INFO

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Add console handler if none exists
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(format)
        handler.setFormatter(formatter)
        root.addHandler(handler)


def get_logger(name: str, **kwargs: Any) -> "Logger":
    """Get a logger instance for the specified name.

    This is a convenience function that returns a Logger instance
    for the specified name. It's equivalent to calling
    Logger.get_logger(name, **kwargs).

    Args:
        name: Name for the logger, typically __name__
        **kwargs: Additional configuration options

    Returns:
        Logger instance
    """
    return Logger.get_logger(name, **kwargs)


__all__ = [
    "LogLevel",
    "Logger",
    "LogRecord",
    "setup_logging",
    "get_logger",
]
