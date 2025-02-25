"""Logging system for the Pepperpy framework.

This module provides logging functionality with structured logging support.
"""

import logging
import sys
from typing import Any, Dict, Optional, cast

# Configure default logging format
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


class StructuredLogger(logging.Logger):
    """Logger with structured logging support."""

    def __init__(self, name: str, level: int = logging.NOTSET) -> None:
        """Initialize logger.

        Args:
            name: Logger name
            level: Logging level
        """
        super().__init__(name, level)
        self._context: dict[str, Any] = {}

    def contextualize(self, **context: Any) -> "StructuredLoggerContext":
        """Add context to log messages.

        Args:
            **context: Context key-value pairs

        Returns:
            Context manager for scoped logging context
        """
        return StructuredLoggerContext(self, context)

    def _log(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info: BaseException | None = None,
        extra: dict[str, Any] | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        """Log a message with context.

        Args:
            level: Logging level
            msg: Message to log
            args: Message format args
            exc_info: Exception info
            extra: Extra data
            stack_info: Include stack info
            stacklevel: Stack level
        """
        if extra is None:
            extra = {}
        extra.update(self._context)
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)


class StructuredLoggerContext:
    """Context manager for scoped logging context."""

    def __init__(self, logger: StructuredLogger, context: dict[str, Any]) -> None:
        """Initialize context.

        Args:
            logger: Logger instance
            context: Context data
        """
        self.logger = logger
        self.context = context
        self.old_context: dict[str, Any] = {}

    def __enter__(self) -> None:
        """Enter context scope."""
        self.old_context = self.logger._context.copy()
        self.logger._context.update(self.context)

    def __exit__(self, *args: Any) -> None:
        """Exit context scope."""
        self.logger._context = self.old_context


def get_logger(name: str) -> StructuredLogger:
    """Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logging.setLoggerClass(StructuredLogger)
    logger = logging.getLogger(name)

    # Add console handler if no handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
        logger.addHandler(handler)

    return cast(StructuredLogger, logger)


__all__ = ["StructuredLogger", "StructuredLoggerContext", "get_logger"]
