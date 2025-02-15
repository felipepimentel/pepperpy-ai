"""Centralized logging system.

This module provides a unified logging interface with structured logging support,
context tracking, and consistent formatting across the application.
"""

import logging
import sys
from typing import Any, Dict, Optional, Union

import structlog
from structlog.types import Processor, WrappedLogger

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.monitoring.types import MonitoringError

__all__ = [
    "LoggingError",
    "get_logger",
    "logger_manager",
    "setup_logging",
]


class LoggingError(MonitoringError):
    """Error raised by logging operations."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            details: Additional error details

        """
        super().__init__(message, "LOGGING_ERROR", details)


def setup_logging(
    level: Union[str, int] = logging.INFO,
    enable_json: bool = False,
) -> None:
    """Set up the logging system.

    Args:
        level: Logging level (default: INFO)
        enable_json: Whether to use JSON formatting (default: False)

    Raises:
        LoggingError: If setup fails

    """
    try:
        # Convert string level to int if needed
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        # Configure standard logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=level,
        )

        # Configure structlog processors
        processors: list[Processor] = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]

        if enable_json:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(
                structlog.dev.ConsoleRenderer(
                    colors=True,
                    exception_formatter=structlog.dev.plain_traceback,
                )
            )

        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    except Exception as e:
        raise LoggingError("Failed to set up logging", {"error": str(e)}) from e


class LoggerManager(Lifecycle):
    """Manager for creating and configuring loggers.

    This class provides a centralized way to create loggers with consistent
    configuration and context tracking.
    """

    def __init__(self) -> None:
        """Initialize the logger manager."""
        super().__init__()
        self._loggers: Dict[str, WrappedLogger] = {}
        self._global_context: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize the logger manager.

        This sets up the default logging configuration if not already configured.

        Raises:
            LoggingError: If initialization fails

        """
        try:
            # Set up default logging if not configured
            if not logging.getLogger().handlers:
                setup_logging()
        except Exception as e:
            raise LoggingError(
                "Failed to initialize logger manager", {"error": str(e)}
            ) from e

    async def cleanup(self) -> None:
        """Clean up logger resources."""
        self._loggers.clear()
        self._global_context.clear()

    def get_logger(
        self,
        name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> WrappedLogger:
        """Get a logger with the given name and context.

        Args:
            name: Logger name
            context: Optional context to bind to the logger

        Returns:
            Configured logger instance

        Raises:
            LoggingError: If logger creation fails

        """
        try:
            if name not in self._loggers:
                logger = structlog.get_logger(name)

                # Bind global context
                if self._global_context:
                    logger = logger.bind(**self._global_context)

                self._loggers[name] = logger

            logger = self._loggers[name]

            # Bind additional context if provided
            if context:
                logger = logger.bind(**context)

            return logger
        except Exception as e:
            raise LoggingError(
                f"Failed to get logger: {name}", {"error": str(e), "context": context}
            ) from e

    def add_global_context(self, **context: Any) -> None:
        """Add context that will be included in all loggers.

        Args:
            **context: Context key-value pairs

        """
        self._global_context.update(context)

        # Update existing loggers with new context
        for name, logger in self._loggers.items():
            self._loggers[name] = logger.bind(**context)

    def clear_global_context(self) -> None:
        """Clear all global context."""
        self._global_context.clear()

        # Reset existing loggers
        for name in self._loggers:
            self._loggers[name] = structlog.get_logger(name)


# Global logger manager instance
logger_manager = LoggerManager()


def get_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None,
) -> WrappedLogger:
    """Get a logger with the given name and context.

    This is a convenience function that uses the global logger manager.

    Args:
        name: Logger name
        context: Optional context to bind to the logger

    Returns:
        Configured logger instance

    Raises:
        LoggingError: If logger creation fails

    """
    return logger_manager.get_logger(name, context)
