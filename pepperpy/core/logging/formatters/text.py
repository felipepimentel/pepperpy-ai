"""
Text formatter for log records.
"""

from pepperpy.core.logging.base import LogFormatter
from pepperpy.core.logging.types import LogRecord


class TextFormatter(LogFormatter):
    """Formats log records as human-readable text."""

    def __init__(
        self,
        format_string: str | None = None,
        time_format: str = "%Y-%m-%d %H:%M:%S",
        include_context: bool = True,
    ):
        self.format_string = format_string or "[{timestamp}] {level:<8} {message}"
        self.time_format = time_format
        self.include_context = include_context

    def _format_context(self, context: dict) -> str:
        """Format context dictionary as a string."""
        if not context:
            return ""

        items = []
        for key, value in sorted(context.items()):
            items.append(f"{key}={value}")

        return f" [{' '.join(items)}]"

    def _format_exception(self, record: LogRecord) -> str:
        """Format exception information."""
        if not record.exception_info:
            return ""

        return f"\nException: {record.exception_info.__class__.__name__}: {record.exception_info!s}"

    def _format_stack(self, record: LogRecord) -> str:
        """Format stack information."""
        if not record.stack_info:
            return ""

        return f"\nStack trace:\n{record.stack_info}"

    def _format_location(self, record: LogRecord) -> str:
        """Format code location information."""
        if not (record.module and record.function):
            return ""

        location = f"{record.module}.{record.function}"
        if record.line_number is not None:
            location = f"{location}:{record.line_number}"

        return f" ({location})"

    def format(self, record: LogRecord) -> str:
        """Format a log record as text."""
        # Format basic information
        output = self.format_string.format(
            timestamp=record.timestamp.strftime(self.time_format),
            level=record.level.value,
            message=record.message,
            logger=record.logger_name,
        )

        # Add location if available
        output += self._format_location(record)

        # Add context if enabled
        if self.include_context:
            output += self._format_context(record.context)

        # Add exception information if available
        output += self._format_exception(record)

        # Add stack trace if available
        output += self._format_stack(record)

        return output
