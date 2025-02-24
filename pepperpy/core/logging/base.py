"""
Base classes for the logging system.
"""

import inspect
import sys
from abc import ABC, abstractmethod
from typing import Any

from pepperpy.core.logging.errors import (
    LogHandlerError,
)
from pepperpy.core.logging.types import LogLevel, LogRecord
from pepperpy.core.metrics.unified import MetricsManager


class LogFilter(ABC):
    """Abstract base class for log filters."""

    @abstractmethod
    def filter(self, record: LogRecord) -> bool:
        """Filter a log record."""
        pass


class LogFormatter(ABC):
    """Abstract base class for log formatters."""

    @abstractmethod
    def format(self, record: LogRecord) -> str:
        """Format a log record."""
        pass


class LogHandler(ABC):
    """Abstract base class for log handlers."""

    def __init__(self):
        self.formatter: LogFormatter | None = None
        self.filters: list[LogFilter] = []
        self._metrics = MetricsManager.get_instance()

    def set_formatter(self, formatter: LogFormatter) -> None:
        """Set the formatter for this handler."""
        self.formatter = formatter

    def add_filter(self, filter_: LogFilter) -> None:
        """Add a filter to this handler."""
        if filter_ not in self.filters:
            self.filters.append(filter_)

    def remove_filter(self, filter_: LogFilter) -> None:
        """Remove a filter from this handler."""
        if filter_ in self.filters:
            self.filters.remove(filter_)

    def should_log(self, record: LogRecord) -> bool:
        """Check if the record should be logged."""
        return all(f.filter(record) for f in self.filters)

    def handle(self, record: LogRecord) -> None:
        """Handle a log record."""
        try:
            if self.should_log(record):
                if self.formatter:
                    formatted = self.formatter.format(record)
                    self.emit(formatted)
                else:
                    self.emit(str(record))

                self._metrics.record_metric(
                    "log_handled",
                    1,
                    {
                        "handler": self.__class__.__name__,
                        "level": str(record.level),
                    },
                )
        except Exception as e:
            raise LogHandlerError(self.__class__.__name__, "handle", e)

    @abstractmethod
    def emit(self, message: str) -> None:
        """Emit a log message."""
        pass

    def flush(self) -> None:
        """Flush any buffered log records."""
        pass

    def close(self) -> None:
        """Close the handler and release resources."""
        self.flush()


class Logger:
    """A logger instance."""

    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.level = level
        self.handlers: list[LogHandler] = []
        self.context: dict[str, Any] = {}
        self._metrics = MetricsManager.get_instance()

    def add_handler(self, handler: LogHandler) -> None:
        """Add a handler to this logger."""
        if handler not in self.handlers:
            self.handlers.append(handler)

    def remove_handler(self, handler: LogHandler) -> None:
        """Remove a handler from this logger."""
        if handler in self.handlers:
            self.handlers.remove(handler)

    def set_level(self, level: LogLevel) -> None:
        """Set the log level."""
        self.level = level

    def set_context(self, **kwargs) -> None:
        """Set context values."""
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context values."""
        self.context.clear()

    def _create_record(self, level: LogLevel, message: str, **kwargs) -> LogRecord:
        """Create a log record."""
        frame = inspect.currentframe()
        if frame:
            frame = frame.f_back
            if frame:
                frame = frame.f_back

        module = frame.f_globals["__name__"] if frame else None
        function = frame.f_code.co_name if frame else None
        line_number = frame.f_lineno if frame else None

        context = self.context.copy()
        context.update(kwargs)

        return LogRecord(
            level=level,
            message=message,
            logger_name=self.name,
            module=module,
            function=function,
            line_number=line_number,
            context=context,
        )

    def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """Log a message at the specified level."""
        if level.numeric_value < self.level.numeric_value:
            return

        record = self._create_record(level, message, **kwargs)

        for handler in self.handlers:
            try:
                handler.handle(record)
            except Exception as e:
                sys.stderr.write(
                    f"Error in handler {handler.__class__.__name__}: {e!s}\n"
                )

        self._metrics.record_metric(
            "log_message",
            1,
            {
                "logger": self.name,
                "level": str(level),
            },
        )

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self.log(LogLevel.CRITICAL, message, **kwargs)

    def exception(
        self, message: str, exc_info: Exception | None = None, **kwargs
    ) -> None:
        """Log an exception."""
        if exc_info is None:
            exc_info = sys.exc_info()[1]

        if exc_info:
            kwargs["exception_info"] = exc_info

        self.error(message, **kwargs)
