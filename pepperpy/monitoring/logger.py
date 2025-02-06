"""Logging configuration for the Pepperpy framework.

This module provides structured logging functionality using loguru,
with support for context-aware logging and custom formatting.
"""

import sys
from contextlib import contextmanager
from typing import Any

from loguru import Logger, logger

# Configure default logger
logger.remove()
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    level="INFO",
)

# Add file handler for persistent logging
logger.add(
    "logs/pepperpy.log",
    rotation="1 day",
    retention="1 month",
    compression="zip",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    ),
    level="DEBUG",
)


class ContextLogger:
    """Context-aware logger that maintains context across log entries."""

    def __init__(self) -> None:
        """Initialize the context logger."""
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> None:
        """Bind context values to the logger.

        Args:
            **kwargs: Context key-value pairs.
        """
        self._context.update(kwargs)

    def unbind(self, *keys: str) -> None:
        """Remove context values from the logger.

        Args:
            *keys: Context keys to remove.
        """
        for key in keys:
            self._context.pop(key, None)

    @contextmanager
    def contextualize(self, **kwargs: Any) -> Any:
        """Temporarily bind context values.

        Args:
            **kwargs: Context key-value pairs.

        Yields:
            None
        """
        original = self._context.copy()
        self.bind(**kwargs)
        try:
            yield
        finally:
            self._context = original

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        """Internal logging method.

        Args:
            level: Log level.
            message: Log message.
            **kwargs: Additional log fields.
        """
        context = {**self._context, **kwargs}
        logger.opt(depth=1).log(level, message, **context)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: Log message.
            **kwargs: Additional log fields.
        """
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            message: Log message.
            **kwargs: Additional log fields.
        """
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            message: Log message.
            **kwargs: Additional log fields.
        """
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: Log message.
            **kwargs: Additional log fields.
        """
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message.

        Args:
            message: Log message.
            **kwargs: Additional log fields.
        """
        self._log("CRITICAL", message, **kwargs)


# Create global context logger instance
context_logger = ContextLogger()


def get_logger(name: str) -> Logger:
    """Get a logger instance.

    Args:
        name: Name of the logger

    Returns:
        Logger instance
    """
    return logger.bind(name=name)
