"""Logging configuration for the Pepperpy framework.

This module provides structured logging functionality using loguru,
with support for context-aware logging and custom formatting.
"""

import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from loguru import logger

# Configure default logger
logger.remove()
logger.add(
    sys.stderr,
    format="{time} | {level} | {message} | {extra}",
    level="INFO",
)


@contextmanager
def contextualize(**context: str) -> Generator[None, None, None]:
    """Add context to log messages.

    Args:
        **context: Context key-value pairs to add to log messages.

    Yields:
        None: Context manager that adds context to log messages.
    """
    token = logger.bind(**context)
    try:
        with token.contextualize():
            yield
    finally:
        pass


class StructuredLogger:
    """Structured logger with context management."""

    def __init__(self) -> None:
        """Initialize the logger."""
        self._logger = logger

    def bind(self, **context: str) -> Any:
        """Bind context to logger.

        Args:
            **context: Context key-value pairs to bind.

        Returns:
            Logger with bound context.
        """
        return self._logger.bind(**context)

    def debug(self, message: str, **context: str) -> None:
        """Log debug message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        self._logger.debug(message, **context)

    def info(self, message: str, **context: str) -> None:
        """Log info message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        self._logger.info(message, **context)

    def warning(self, message: str, **context: str) -> None:
        """Log warning message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        self._logger.warning(message, **context)

    def error(self, message: str, **context: str) -> None:
        """Log error message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        self._logger.error(message, **context)

    def exception(self, message: str, **context: str) -> None:
        """Log exception message.

        Args:
            message: Message to log.
            **context: Additional context.
        """
        self._logger.exception(message, **context)


# Create default logger instances
structured_logger = StructuredLogger()
context_logger = logger.bind()


def get_logger(name: str) -> Any:
    """Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logger.bind(name=name)
