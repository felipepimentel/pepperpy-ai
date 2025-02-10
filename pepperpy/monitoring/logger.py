"""Logging configuration for the Pepperpy framework.

This module provides structured logging functionality using Python's standard logging,
with support for context-aware logging and custom formatting.
"""

import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

# Configure default logger
logger = logging.getLogger("pepperpy")
logger.setLevel(logging.INFO)

# Configure handler with custom format
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s | %(context)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# Context filter to add extra context to log records
class ContextFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.context = {}

    def filter(self, record):
        record.context = str(self.context)
        return True


context_filter = ContextFilter()
logger.addFilter(context_filter)


@contextmanager
def contextualize(**context: str) -> Generator[None, None, None]:
    """Add context to log messages.

    Args:
        **context: Context key-value pairs to add to log messages.

    Yields:
        None: Context manager that adds context to log messages.
    """
    old_context = context_filter.context.copy()
    context_filter.context.update(context)
    try:
            yield
    finally:
        context_filter.context = old_context


class StructuredLogger:
    """Structured logger with context management."""

    def __init__(self) -> None:
        """Initialize the logger."""
        self._logger = logger
        self._context = {}

    def bind(self, **context: str) -> Any:
        """Bind context to logger.

        Args:
            **context: Context key-value pairs to bind.

        Returns:
            Logger with bound context.
        """
        new_logger = StructuredLogger()
        new_logger._context = self._context.copy()
        new_logger._context.update(context)
        return new_logger

    def debug(self, message: str, **context: str) -> None:
        """Log debug message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        with contextualize(**{**self._context, **context}):
            self._logger.debug(message)

    def info(self, message: str, **context: str) -> None:
        """Log info message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        with contextualize(**{**self._context, **context}):
            self._logger.info(message)

    def warning(self, message: str, **context: str) -> None:
        """Log warning message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        with contextualize(**{**self._context, **context}):
            self._logger.warning(message)

    def error(self, message: str, **context: str) -> None:
        """Log error message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        with contextualize(**{**self._context, **context}):
            self._logger.error(message)

    def exception(self, message: str, **context: str) -> None:
        """Log exception message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        with contextualize(**{**self._context, **context}):
            self._logger.exception(message)


# Create default logger instances
structured_logger = StructuredLogger()
context_logger = StructuredLogger().bind()


def get_logger(name: str) -> Any:
    """Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return StructuredLogger().bind(name=name)
