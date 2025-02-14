"""Factory for creating structured loggers."""

import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional, Set, TextIO

from pepperpy.core.lifecycle import Lifecycle

from .types import LogLevel, LogRecord


class LogFilter:
    """Filter for log records."""

    def __init__(self, min_level: LogLevel = LogLevel.INFO) -> None:
        """Initialize the filter.

        Args:
            min_level: Minimum log level to allow

        """
        self.min_level = min_level

    def should_log(self, record: LogRecord) -> bool:
        """Check if a record should be logged.

        Args:
            record: Log record to check

        Returns:
            True if the record should be logged

        """
        return record.level.value >= self.min_level.value


class LogFormatter:
    """Formatter for log records."""

    def format(self, record: LogRecord) -> str:
        """Format a log record.

        Args:
            record: Log record to format

        Returns:
            Formatted log string

        """
        base = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.level.name,
            "message": record.message,
            "logger": record.module,
        }

        if record.context:
            base["context"] = json.dumps(record.context)
        if record.metadata:
            base["metadata"] = json.dumps(record.metadata)
        if record.error:
            base["error"] = str(record.error)

        return json.dumps(base)


class Logger:
    """A structured logger with context support.

    This class provides structured logging with context and metadata.
    It supports multiple output formats and destinations.

    Attributes:
        name: Logger name
        context: Default context for all logs
        metadata: Default metadata for all logs

    """

    def __init__(
        self,
        name: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        output: Optional[TextIO] = None,
        min_level: LogLevel = LogLevel.INFO,
    ) -> None:
        """Initialize the logger.

        Args:
            name: Logger name
            context: Optional default context
            metadata: Optional default metadata
            output: Optional output stream (defaults to sys.stderr)
            min_level: Minimum log level (defaults to INFO)

        """
        self.name = name
        self.context = context or {}
        self.metadata = metadata or {}
        self.output = output or sys.stderr
        self._filter = LogFilter(min_level)
        self._formatter = LogFormatter()
        self._handlers: Set[TextIO] = {self.output}

    def add_handler(self, handler: TextIO) -> None:
        """Add an output handler.

        Args:
            handler: Output handler to add

        """
        self._handlers.add(handler)

    def remove_handler(self, handler: TextIO) -> None:
        """Remove an output handler.

        Args:
            handler: Output handler to remove

        """
        if handler != self.output:  # Don't remove default handler
            self._handlers.discard(handler)

    def _log(
        self,
        level: LogLevel,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Log a message.

        Args:
            level: Log level
            message: Log message
            context: Optional additional context
            metadata: Optional additional metadata
            error: Optional error to log

        """
        # Merge contexts and metadata
        merged_context = {**self.context, **(context or {})}
        merged_metadata = {**self.metadata, **(metadata or {})}

        # Create record
        record = LogRecord(
            module=self.name,
            level=level,
            message=message,
            context=merged_context,
            metadata=merged_metadata,
            error=error,
        )

        # Check if should log
        if not self._filter.should_log(record):
            return

        # Format and write
        formatted = self._formatter.format(record)
        for handler in self._handlers:
            handler.write(formatted + "\n")
            handler.flush()

    def debug(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Log a debug message.

        Args:
            message: Log message
            context: Optional additional context
            metadata: Optional additional metadata
            error: Optional error to log

        """
        self._log(
            LogLevel.DEBUG, message, context=context, metadata=metadata, error=error
        )

    def info(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Log an info message.

        Args:
            message: Log message
            context: Optional additional context
            metadata: Optional additional metadata
            error: Optional error to log

        """
        self._log(
            LogLevel.INFO, message, context=context, metadata=metadata, error=error
        )

    def warning(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Log a warning message.

        Args:
            message: Log message
            context: Optional additional context
            metadata: Optional additional metadata
            error: Optional error to log

        """
        self._log(
            LogLevel.WARNING, message, context=context, metadata=metadata, error=error
        )

    def error(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Log an error message.

        Args:
            message: Log message
            context: Optional additional context
            metadata: Optional additional metadata
            error: Optional error to log

        """
        self._log(
            LogLevel.ERROR, message, context=context, metadata=metadata, error=error
        )


class LoggerFactory(Lifecycle):
    """Factory for creating loggers.

    This class manages logger creation and configuration.
    It ensures consistent logging setup across the application.

    Attributes:
        loggers: Currently active loggers

    """

    def __init__(self) -> None:
        """Initialize the factory."""
        super().__init__()
        self._loggers: Dict[str, Logger] = {}
        self._default_context: Dict[str, Any] = {}
        self._default_metadata: Dict[str, Any] = {}
        self._default_level = LogLevel.INFO
        self._default_output = sys.stderr

    def configure(
        self,
        *,
        default_level: Optional[LogLevel] = None,
        default_context: Optional[Dict[str, Any]] = None,
        default_metadata: Optional[Dict[str, Any]] = None,
        default_output: Optional[TextIO] = None,
    ) -> None:
        """Configure default logger settings.

        Args:
            default_level: Default minimum log level
            default_context: Default context for all loggers
            default_metadata: Default metadata for all loggers
            default_output: Default output stream

        """
        if default_level is not None:
            self._default_level = default_level
        if default_context is not None:
            self._default_context = default_context
        if default_metadata is not None:
            self._default_metadata = default_metadata
        if default_output is not None:
            self._default_output = default_output

    def get_logger(
        self,
        name: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        min_level: Optional[LogLevel] = None,
        output: Optional[TextIO] = None,
    ) -> Logger:
        """Get or create a logger.

        Args:
            name: Logger name
            context: Optional context (merged with defaults)
            metadata: Optional metadata (merged with defaults)
            min_level: Optional minimum level (overrides default)
            output: Optional output stream (overrides default)

        Returns:
            Logger instance

        """
        if name not in self._loggers:
            merged_context = {**self._default_context, **(context or {})}
            merged_metadata = {**self._default_metadata, **(metadata or {})}

            self._loggers[name] = Logger(
                name,
                context=merged_context,
                metadata=merged_metadata,
                min_level=min_level or self._default_level,
                output=output or self._default_output,
            )

        return self._loggers[name]

    async def initialize(self) -> None:
        """Initialize the factory."""
        # Nothing to initialize yet
        pass

    async def cleanup(self) -> None:
        """Clean up the factory."""
        # Clear all loggers
        self._loggers.clear()
