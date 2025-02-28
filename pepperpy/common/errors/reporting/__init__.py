"""Error reporting functionality.

This module provides tools for formatting and reporting errors.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from pepperpy.common.errors.unified import PepperError


@dataclass
class ErrorReport:
    """Structured error report."""

    error: Exception
    timestamp: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)
    traceback: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary.

        Returns:
            Dictionary representation of the report
        """
        return {
            "error_type": type(self.error).__name__,
            "message": str(self.error),
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "traceback": self.traceback,
        }


class ErrorFormatter:
    """Formats errors for reporting."""

    def __init__(self, include_traceback: bool = True) -> None:
        """Initialize formatter.

        Args:
            include_traceback: Whether to include traceback in reports
        """
        self.include_traceback = include_traceback

    def format_error(self, error: Exception, **context: Any) -> ErrorReport:
        """Format an error as a report.

        Args:
            error: The error to format
            **context: Additional context to include

        Returns:
            Formatted error report
        """
        import traceback

        report = ErrorReport(
            error=error,
            context=context,
        )

        if self.include_traceback:
            report.traceback = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )

        return report

    def format_as_json(self, error: Exception, **context: Any) -> str:
        """Format error as JSON string.

        Args:
            error: The error to format
            **context: Additional context to include

        Returns:
            JSON string representation
        """
        import json

        report = self.format_error(error, **context)
        return json.dumps(report.to_dict(), indent=2)

    def format_as_text(self, error: Exception, **context: Any) -> str:
        """Format error as plain text.

        Args:
            error: The error to format
            **context: Additional context to include

        Returns:
            Text representation
        """
        report = self.format_error(error, **context)
        lines = [
            f"Error: {type(error).__name__}",
            f"Message: {error!s}",
            f"Time: {report.timestamp.isoformat()}",
            "Context:",
        ]

        for key, value in report.context.items():
            lines.append(f"  {key}: {value}")

        if report.traceback:
            lines.extend(["", "Traceback:", report.traceback])

        return "\n".join(lines)


__all__ = ["ErrorFormatter", "ErrorReport", "PepperError"]
