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
import os
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union, TextIO

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


# Create a verbosity level enum for consistent use across modules
class VerbosityLevel(Enum):
    """Verbosity levels for all PepperPy operations."""
    SILENT = 0    # No output
    ERROR = 1     # Only errors
    INFO = 2      # Basic information
    DEBUG = 3     # Detailed information
    VERBOSE = 4   # Very detailed information

    @classmethod
    def from_string(cls, level_str: str) -> "VerbosityLevel":
        """Convert string to VerbosityLevel.
        
        Args:
            level_str: String representation of verbosity level

        Returns:
            Corresponding VerbosityLevel
        """
        level_map = {
            "silent": cls.SILENT,
            "error": cls.ERROR,
            "info": cls.INFO,
            "debug": cls.DEBUG,
            "verbose": cls.VERBOSE
        }
        return level_map.get(level_str.lower(), cls.INFO)

# Mapping from VerbosityLevel to logging level
LEVEL_MAP = {
    VerbosityLevel.SILENT: logging.CRITICAL,
    VerbosityLevel.ERROR: logging.ERROR,
    VerbosityLevel.INFO: logging.INFO,
    VerbosityLevel.DEBUG: logging.DEBUG,
    VerbosityLevel.VERBOSE: logging.DEBUG  # Python doesn't have a more verbose level
}

class LogManager:
    """Centralized logging management for PepperPy."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Create a singleton instance."""
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, 
                 verbosity: Union[VerbosityLevel, int, str] = VerbosityLevel.INFO,
                 log_file: Optional[Union[str, Path]] = None,
                 log_format: str = "%(levelname)s - %(message)s",
                 **kwargs):
        """Initialize the log manager if not already initialized.
        
        Args:
            verbosity: Verbosity level for logging
            log_file: Optional file to write logs to
            log_format: Format for log messages
            **kwargs: Additional configuration options
        """
        if LogManager._initialized:
            return
            
        # Convert verbosity to VerbosityLevel if needed
        if isinstance(verbosity, int):
            try:
                self.verbosity = VerbosityLevel(verbosity)
            except ValueError:
                self.verbosity = VerbosityLevel.INFO
        elif isinstance(verbosity, str):
            self.verbosity = VerbosityLevel.from_string(verbosity)
        else:
            self.verbosity = verbosity
            
        # Set up root logger
        self.root_logger = logging.getLogger("pepperpy")
        self.root_logger.setLevel(LEVEL_MAP[self.verbosity])
        
        # Remove existing handlers to avoid duplicates
        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        self.root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            self.set_log_file(log_file, log_format)
            
        LogManager._initialized = True
        
    def set_verbosity(self, level: Union[VerbosityLevel, int, str]) -> None:
        """Set the verbosity level.
        
        Args:
            level: New verbosity level
        """
        if isinstance(level, int):
            try:
                self.verbosity = VerbosityLevel(level)
            except ValueError:
                self.verbosity = VerbosityLevel.INFO
        elif isinstance(level, str):
            self.verbosity = VerbosityLevel.from_string(level)
        else:
            self.verbosity = level
            
        self.root_logger.setLevel(LEVEL_MAP[self.verbosity])
        
    def set_log_file(self, file_path: Union[str, Path], log_format: Optional[str] = None) -> None:
        """Set a log file for output.
        
        Args:
            file_path: Path to log file
            log_format: Optional format for log messages
        """
        # Ensure directory exists
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing file handlers
        for handler in self.root_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                self.root_logger.removeHandler(handler)
        
        # Add new file handler
        file_handler = logging.FileHandler(path)
        file_handler.setFormatter(logging.Formatter(
            log_format or "%(asctime)s - %(levelname)s - %(message)s"))
        self.root_logger.addHandler(file_handler)
        
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger for a specific module.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Configured logger instance
        """
        return logging.getLogger(f"pepperpy.{name}")
    
    def log(self, level: VerbosityLevel, message: str, *args, **kwargs) -> None:
        """Log a message at the specified level.
        
        Args:
            level: Verbosity level
            message: Message to log
            *args: Additional args passed to logger
            **kwargs: Additional kwargs passed to logger
        """
        if level.value <= self.verbosity.value:
            if level == VerbosityLevel.SILENT:
                return
            elif level == VerbosityLevel.ERROR:
                self.root_logger.error(message, *args, **kwargs)
            elif level == VerbosityLevel.INFO:
                self.root_logger.info(message, *args, **kwargs)
            elif level == VerbosityLevel.DEBUG:
                self.root_logger.debug(message, *args, **kwargs)
            elif level == VerbosityLevel.VERBOSE:
                self.root_logger.debug(f"[VERBOSE] {message}", *args, **kwargs)

# Initialize the global log manager
log_manager = LogManager()

def get_log_manager() -> LogManager:
    """Get the global log manager instance.
    
    Returns:
        LogManager instance
    """
    return log_manager

def configure_logging(
    verbosity: Union[VerbosityLevel, int, str] = VerbosityLevel.INFO,
    log_file: Optional[Union[str, Path]] = None,
    log_format: str = "%(levelname)s - %(message)s"
) -> LogManager:
    """Configure global logging settings.
    
    Args:
        verbosity: Verbosity level for logging
        log_file: Optional file to write logs to
        log_format: Format for log messages
        
    Returns:
        Configured LogManager instance
    """
    global log_manager
    log_manager = LogManager(verbosity=verbosity, log_file=log_file, log_format=log_format)
    return log_manager

def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return log_manager.get_logger(name)

__all__ = [
    "LogLevel",
    "Logger",
    "LogRecord",
    "setup_logging",
    "get_logger",
]
