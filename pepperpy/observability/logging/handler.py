"""Logging handler implementation.

This module provides a structured logging handler that implements
the logging interface of the observability system.

Example:
    >>> handler = StructuredLogHandler()
    >>> handler.log(
    ...     "Request processed",
    ...     LogLevel.INFO,
    ...     {"request_id": "123"}
    ... )
    >>> logs = handler.get_logs(time.time() - 60, time.time())
    >>> assert len(logs) > 0
"""

import time

import structlog

from ..errors import LoggingError
from ..types import Context, LogLevel, LogRecord


class StructuredLogHandler:
    """Structured logging handler using structlog.

    This class implements structured logging using the structlog library.
    It provides methods for logging messages with context and retrieving logs.

    Attributes:
        logger: The structlog logger instance
        _logs: List of recorded log records

    Example:
        >>> handler = StructuredLogHandler()
        >>> handler.log(
        ...     "Request processed",
        ...     LogLevel.INFO,
        ...     {"request_id": "123"}
        ... )
        >>> logs = handler.get_logs(time.time() - 60, time.time())
        >>> assert len(logs) > 0
    """

    def __init__(self) -> None:
        """Initialize logging handler."""
        self.logger = structlog.get_logger()
        self._logs: list[LogRecord] = []

    def log(
        self,
        message: str,
        level: LogLevel,
        context: Context | None = None,
    ) -> None:
        """Log a message with structured context.

        Args:
            message: Log message
            level: Log level
            context: Optional structured context

        Raises:
            LoggingError: If logging fails
        """
        try:
            log_fn = {
                LogLevel.DEBUG: self.logger.debug,
                LogLevel.INFO: self.logger.info,
                LogLevel.WARNING: self.logger.warning,
                LogLevel.ERROR: self.logger.error,
                LogLevel.CRITICAL: self.logger.critical,
            }[level]

            log_fn(
                message,
                **(context or {}),
            )

            self._logs.append(
                LogRecord(
                    message=message,
                    level=level,
                    timestamp=time.time(),
                    context=context or {},
                )
            )

        except Exception as e:
            raise LoggingError(f"Failed to log message: {e}")

    def get_logs(
        self,
        start_time: float,
        end_time: float,
        level: LogLevel | None = None,
    ) -> list[LogRecord]:
        """Get logs within a time range.

        Args:
            start_time: Start time in seconds since epoch
            end_time: End time in seconds since epoch
            level: Optional log level filter

        Returns:
            List of log records matching the criteria

        Raises:
            LoggingError: If log retrieval fails
        """
        try:
            filtered_logs = [
                log
                for log in self._logs
                if start_time <= log.timestamp <= end_time
                and (level is None or log.level == level)
            ]
            return filtered_logs

        except Exception as e:
            raise LoggingError(f"Failed to get logs: {e}")
