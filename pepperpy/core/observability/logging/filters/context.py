"""Context filter for logging.

This module provides a context filter that filters log records based on
their context values.
"""

from typing import Any

from pepperpy.monitoring.logging.base import LogRecord


class ContextFilter:
    """Context log filter."""

    def __init__(self, context: dict[str, Any]) -> None:
        """Initialize context filter.

        Args:
            context: Context key-value pairs to match
        """
        self.context = context

    def filter(self, record: LogRecord) -> bool:
        """Filter log record.

        Args:
            record: Log record to filter

        Returns:
            True if record should be logged
        """
        for key, value in self.context.items():
            if key not in record.context or record.context[key] != value:
                return False
        return True


# Export public API
__all__ = ["ContextFilter"]
