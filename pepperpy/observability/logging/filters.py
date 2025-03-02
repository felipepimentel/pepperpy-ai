"""Logging filters package.

This module provides filters for logging records based on
their context values and log levels.
"""

from typing import Any, Dict, Set

from pepperpy.observability.logging.base import LogLevel, LogRecord


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


class LevelFilter:
    """Level log filter."""

    def __init__(self, levels: set[LogLevel]) -> None:
        """Initialize level filter.

        Args:
            levels: Set of allowed log levels
        """
        self.levels = levels

    def filter(self, record: LogRecord) -> bool:
        """Filter log record.

        Args:
            record: Log record to filter

        Returns:
            True if record should be logged
        """
        return record.level in self.levels


# Export public API
__all__ = [
    "ContextFilter",
    "LevelFilter",
]
