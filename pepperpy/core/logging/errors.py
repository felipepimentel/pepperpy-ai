"""
Error classes for the logging system.
"""

from pepperpy.core.errors.unified import PepperpyError
from pepperpy.core.logging.types import LogLevel


class LoggingError(PepperpyError):
    """Base error class for logging-related errors."""

    pass


class LoggerNotFoundError(LoggingError):
    """Error raised when a logger is not found."""

    def __init__(self, logger_name: str):
        self.logger_name = logger_name
        super().__init__(f"Logger not found: {logger_name}")


class HandlerNotFoundError(LoggingError):
    """Error raised when a handler is not found."""

    def __init__(self, handler_name: str):
        self.handler_name = handler_name
        super().__init__(f"Handler not found: {handler_name}")


class FormatterNotFoundError(LoggingError):
    """Error raised when a formatter is not found."""

    def __init__(self, formatter_name: str):
        self.formatter_name = formatter_name
        super().__init__(f"Formatter not found: {formatter_name}")


class FilterNotFoundError(LoggingError):
    """Error raised when a filter is not found."""

    def __init__(self, filter_name: str):
        self.filter_name = filter_name
        super().__init__(f"Filter not found: {filter_name}")


class InvalidLogLevelError(LoggingError):
    """Error raised when an invalid log level is used."""

    def __init__(self, level: str):
        self.level = level
        super().__init__(
            f"Invalid log level: {level}. Valid levels are: {[l.value for l in LogLevel]}"
        )


class LogConfigError(LoggingError):
    """Error raised when there is a configuration error."""

    def __init__(self, message: str):
        super().__init__(f"Log configuration error: {message}")


class LogHandlerError(LoggingError):
    """Error raised when a handler operation fails."""

    def __init__(self, handler_name: str, operation: str, error: Exception):
        self.handler_name = handler_name
        self.operation = operation
        self.original_error = error
        super().__init__(
            f"Handler operation '{operation}' failed for handler '{handler_name}': {error!s}"
        )


class LogFormatterError(LoggingError):
    """Error raised when a formatter operation fails."""

    def __init__(self, formatter_name: str, error: Exception):
        self.formatter_name = formatter_name
        self.original_error = error
        super().__init__(
            f"Formatter operation failed for formatter '{formatter_name}': {error!s}"
        )
