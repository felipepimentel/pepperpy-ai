"""Base interfaces and classes for the PepperPy logging system.

This module defines the core interfaces and base classes for the structured
logging system used throughout PepperPy.
"""

import enum
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


class LogLevel(enum.IntEnum):
    """Standard log levels."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogHandler(ABC):
    """Base class for log handlers.

    Log handlers are responsible for processing log records and
    sending them to appropriate destinations (console, file, etc).
    """

    @abstractmethod
    def handle(self, record: Dict[str, Any]) -> None:
        """Handle a log record.

        Args:
            record: The log record to handle
        """
        pass


class ConsoleLogHandler(LogHandler):
    """Log handler that outputs to the console."""

    def handle(self, record: Dict[str, Any]) -> None:
        """Handle a log record by printing to console.

        Args:
            record: The log record to handle
        """
        timestamp = record.get("timestamp", datetime.now().isoformat())
        level = record.get("level", "INFO")
        message = record.get("message", "")
        context = record.get("context", {})

        if context:
            context_str = json.dumps(context)
            print(f"[{timestamp}] {level}: {message} | {context_str}")
        else:
            print(f"[{timestamp}] {level}: {message}")


class Logger(ABC):
    """Base logger interface.

    This abstract class defines the interface for all loggers in the system.
    """

    @abstractmethod
    def debug(self, message: str, **context: Any) -> None:
        """Log a debug message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        pass

    @abstractmethod
    def info(self, message: str, **context: Any) -> None:
        """Log an info message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        pass

    @abstractmethod
    def warning(self, message: str, **context: Any) -> None:
        """Log a warning message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        pass

    @abstractmethod
    def error(self, message: str, **context: Any) -> None:
        """Log an error message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        pass

    @abstractmethod
    def critical(self, message: str, **context: Any) -> None:
        """Log a critical message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        pass


class StructuredLogger(Logger):
    """Logger implementation with structured output.

    This logger creates structured log records with consistent formatting
    and sends them to registered handlers.
    """

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        handlers: Optional[List[LogHandler]] = None,
    ):
        """Initialize a structured logger.

        Args:
            name: The name of the logger
            level: The minimum log level to process
            handlers: List of handlers to process log records
        """
        self.name = name
        self.level = level
        self.handlers = handlers or [ConsoleLogHandler()]

    def _log(self, level: LogLevel, message: str, **context: Any) -> None:
        """Internal method to create and process a log record.

        Args:
            level: The log level
            message: The log message
            **context: Additional context data
        """
        if level < self.level:
            return

        record = {
            "timestamp": datetime.now().isoformat(),
            "level": level.name,
            "logger": self.name,
            "message": message,
            "context": context,
        }

        for handler in self.handlers:
            handler.handle(record)

    def debug(self, message: str, **context: Any) -> None:
        """Log a debug message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        self._log(LogLevel.DEBUG, message, **context)

    def info(self, message: str, **context: Any) -> None:
        """Log an info message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        self._log(LogLevel.INFO, message, **context)

    def warning(self, message: str, **context: Any) -> None:
        """Log a warning message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        self._log(LogLevel.WARNING, message, **context)

    def error(self, message: str, **context: Any) -> None:
        """Log an error message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        self._log(LogLevel.ERROR, message, **context)

    def critical(self, message: str, **context: Any) -> None:
        """Log a critical message.

        Args:
            message: The message to log
            **context: Additional context data to include in the log
        """
        self._log(LogLevel.CRITICAL, message, **context)


# Global registry of loggers
_loggers: Dict[str, Logger] = {}


def get_logger(name: str) -> Logger:
    """Get a logger instance for a specific module.

    If a logger with the given name already exists, it will be returned.
    Otherwise, a new logger will be created.

    Args:
        name: The name of the logger, typically the module name

    Returns:
        A logger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


def configure_logging(
    level: Union[LogLevel, str, int] = LogLevel.INFO,
    handlers: Optional[List[LogHandler]] = None,
) -> None:
    """Configure global logging settings.

    Args:
        level: The minimum log level to process
        handlers: List of handlers to process log records
    """
    # Convert string or int level to LogLevel enum if needed
    if isinstance(level, str):
        level = LogLevel[level.upper()]
    elif isinstance(level, int):
        level = LogLevel(level)

    # Update all existing loggers
    for logger in _loggers.values():
        if isinstance(logger, StructuredLogger):
            logger.level = level
            if handlers is not None:
                logger.handlers = handlers
