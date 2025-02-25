"""Pepperpy Error Handling System.

This module provides a comprehensive error handling system including:
- Standardized error hierarchy
- Error handling and recovery
- Error reporting and logging

Example:
    >>> from pepperpy.errors import ValidationError, handle_error, report_error
    >>> try:
    ...     raise ValidationError("Invalid input")
    ... except ValidationError as e:
    ...     report_error(e)
    ...     handle_error(e)
"""

from typing import Any, Dict, Optional, Union

from .base import (
    ConfigurationError,
    DatabaseError,
    NetworkError,
    PepperpyError,
    ResourceError,
    SecurityError,
    StateError,
    ValidationError,
)
from .codes import (
    CONFIG_ERRORS,
    RESOURCE_ERRORS,
    STATE_ERRORS,
    VALIDATION_ERRORS,
    ErrorCategory,
    ErrorSeverity,
    generate_error_code,
)
from .handling.base import (
    ErrorHandler,
    ErrorHandlerRegistry,
    global_error_registry,
)
from .recovery.base import (
    FallbackStrategy,
    RecoveryRegistry,
    RecoveryStrategy,
    RetryStrategy,
    global_recovery_registry,
)
from .reporting.base import (
    CompositeReporter,
    ConsoleReporter,
    ErrorReport,
    ErrorReporter,
    FileReporter,
    LoggingReporter,
    global_error_reporter,
)

__all__ = [
    # Base errors
    "PepperpyError",
    "ValidationError",
    "ResourceError",
    "ConfigurationError",
    "StateError",
    "SecurityError",
    "NetworkError",
    "DatabaseError",
    # Error codes
    "ErrorCategory",
    "ErrorSeverity",
    "generate_error_code",
    "VALIDATION_ERRORS",
    "RESOURCE_ERRORS",
    "CONFIG_ERRORS",
    "STATE_ERRORS",
    # Error handling
    "ErrorHandler",
    "ErrorHandlerRegistry",
    "global_error_registry",
    # Error recovery
    "RecoveryStrategy",
    "RetryStrategy",
    "FallbackStrategy",
    "RecoveryRegistry",
    "global_recovery_registry",
    # Error reporting
    "ErrorReport",
    "ErrorReporter",
    "ConsoleReporter",
    "FileReporter",
    "LoggingReporter",
    "CompositeReporter",
    "global_error_reporter",
    # Helper functions
    "handle_error",
    "report_error",
]


def handle_error(error: Exception) -> bool:
    """Handle an error using the global error handler registry.

    Args:
        error: The error to handle. Can be any Exception type.

    Returns:
        bool: True if the error was handled successfully by any handler

    Example:
        >>> error = ValidationError("Invalid input")
        >>> handle_error(error)
        True

    Note:
        The error will be passed to all registered handlers that can handle
        its type. The first successful handler will stop the chain.
    """
    return global_error_registry.handle(error)


def report_error(
    error: PepperpyError, context: dict[str, Any] | None = None
) -> ErrorReport:
    """Report an error using the global error reporter.

    Args:
        error: The error to report. Must be a PepperpyError or subclass.
        context: Optional dictionary with additional context about the error.
            If None, an empty dict will be used.

    Returns:
        ErrorReport: A report containing error details, context, and metadata

    Example:
        >>> error = ValidationError("Invalid input")
        >>> report = report_error(error, {"request_id": "123"})
        >>> assert report.context["request_id"] == "123"

    Note:
        The report will be sent to all configured reporters (console, file,
        logging, etc.) in the global error reporter.
    """
    report = ErrorReport(
        error=error,
        context=context or {},
        stack_trace=error.stack_trace,
        timestamp=error.timestamp,
        handled=False,
        recovery_attempted=False,
        recovery_successful=None,
    )
    global_error_reporter.report(report)
    return report
