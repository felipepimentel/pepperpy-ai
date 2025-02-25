"""Error report formatters for Pepperpy.

This module provides formatters for converting error reports into various formats:
- Base formatter interface
- JSON formatter for machine-readable output
- Text formatter for human-readable output
- Structured formatter for logging systems

Example:
    >>> formatter = JSONFormatter()
    >>> report = ErrorReport(error=error, context={})
    >>> formatted = formatter.format(report)
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from ..base import PepperpyError
from .base import ErrorReport

logger = logging.getLogger(__name__)


class ErrorFormatter(ABC):
    """Abstract base class for error formatters.

    Example:
        >>> class MyFormatter(ErrorFormatter):
        ...     def format(self, report):
        ...         return f"Error: {report.error}"
    """

    @abstractmethod
    def format(self, report: ErrorReport) -> str:
        """Format an error report.

        Args:
            report: The error report to format

        Returns:
            str: The formatted report
        """
        pass


class JSONFormatter(ErrorFormatter):
    """Formats error reports as JSON.

    Args:
        indent: Number of spaces for indentation
        sort_keys: Whether to sort dictionary keys

    Example:
        >>> formatter = JSONFormatter(indent=2)
        >>> print(formatter.format(report))
        {
          "error_type": "ValidationError",
          "message": "Invalid input",
          "timestamp": "2024-03-21T12:00:00"
        }
    """

    def __init__(self, indent: int | None = 2, sort_keys: bool = True) -> None:
        """Initialize a new JSON formatter."""
        self.indent = indent
        self.sort_keys = sort_keys

    def format(self, report: ErrorReport) -> str:
        """Format the report as JSON.

        Args:
            report: The error report to format

        Returns:
            str: JSON-formatted report
        """
        data = self._prepare_data(report)
        return json.dumps(
            data, indent=self.indent, sort_keys=self.sort_keys, default=str
        )

    def _prepare_data(self, report: ErrorReport) -> dict[str, Any]:
        """Prepare report data for JSON serialization."""
        error = report.error
        data = {
            "error_type": error.__class__.__name__,
            "message": str(error),
            "timestamp": report.timestamp.isoformat(),
            "handled": report.handled,
            "recovery_attempted": report.recovery_attempted,
            "recovery_successful": report.recovery_successful,
        }

        if isinstance(error, PepperpyError):
            data.update({
                "error_code": error.code,
                "details": error.details,
                "recovery_hint": error.recovery_hint,
            })

        if report.context:
            data["context"] = report.context

        if report.stack_trace:
            data["stack_trace"] = report.stack_trace

        return data


class TextFormatter(ErrorFormatter):
    """Formats error reports as human-readable text.

    Args:
        include_timestamp: Whether to include timestamp
        include_stack_trace: Whether to include stack trace

    Example:
        >>> formatter = TextFormatter()
        >>> print(formatter.format(report))
        Error: ValidationError
        Message: Invalid input
        Code: VAL-E-001
        Time: 2024-03-21 12:00:00
    """

    def __init__(
        self, include_timestamp: bool = True, include_stack_trace: bool = False
    ) -> None:
        """Initialize a new text formatter."""
        self.include_timestamp = include_timestamp
        self.include_stack_trace = include_stack_trace

    def format(self, report: ErrorReport) -> str:
        """Format the report as text.

        Args:
            report: The error report to format

        Returns:
            str: Text-formatted report
        """
        error = report.error
        lines = [f"Error: {error.__class__.__name__}", f"Message: {error!s}"]

        if isinstance(error, PepperpyError):
            if error.code:
                lines.append(f"Code: {error.code}")
            if error.details:
                lines.append(f"Details: {error.details}")
            if error.recovery_hint:
                lines.append(f"Recovery Hint: {error.recovery_hint}")

        if self.include_timestamp:
            lines.append(f"Time: {report.timestamp}")

        if report.context:
            lines.append(f"Context: {report.context}")

        if report.handled:
            lines.append("Status: Handled")
            if report.recovery_attempted:
                result = "successful" if report.recovery_successful else "failed"
                lines.append(f"Recovery: {result}")

        if self.include_stack_trace and report.stack_trace:
            lines.extend(["", "Stack Trace:", report.stack_trace])

        return "\n".join(lines)


class StructuredFormatter(ErrorFormatter):
    """Formats error reports as structured data for logging systems.

    Args:
        include_stack_trace: Whether to include stack trace

    Example:
        >>> formatter = StructuredFormatter()
        >>> data = formatter.format(report)
        >>> logging.error("Error occurred", extra=data)
    """

    def __init__(self, include_stack_trace: bool = True) -> None:
        """Initialize a new structured formatter."""
        self.include_stack_trace = include_stack_trace

    def format(self, report: ErrorReport) -> dict[str, Any]:
        """Format the report as a structured dictionary.

        Args:
            report: The error report to format

        Returns:
            Dict[str, Any]: Structured report data
        """
        error = report.error
        data = {
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "timestamp": report.timestamp,
            "handled": report.handled,
            "recovery_attempted": report.recovery_attempted,
            "recovery_successful": report.recovery_successful,
        }

        if isinstance(error, PepperpyError):
            data.update({
                "error_code": error.code,
                "error_details": error.details,
                "recovery_hint": error.recovery_hint,
            })

        if report.context:
            data["context"] = report.context

        if self.include_stack_trace and report.stack_trace:
            data["stack_trace"] = report.stack_trace

        return data
