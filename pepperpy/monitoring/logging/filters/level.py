"""Level filter for logging.

This module provides a level filter that filters log records based on
their log level.
"""

from pepperpy.monitoring.logging.base import LogLevel, LogRecord


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
__all__ = ["LevelFilter"]
