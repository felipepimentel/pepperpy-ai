"""Logging configuration for the Pepperpy framework.

This module provides logging functionality and configuration.
"""

import logging
import sys

# Configure default logger
logger = logging.getLogger("pepperpy")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def configure_logging(
    level: str | int = logging.INFO,
    format_str: str | None = None,
    handlers: list[logging.Handler] | None = None,
) -> None:
    """Configure global logging settings.

    Args:
        level: Log level to set (string or integer)
        format_str: Optional custom format string
        handlers: Optional list of handlers to add
    """
    root_logger = logging.getLogger()

    # Set log level
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Add default handler if no handlers provided
    if not handlers:
        handler = logging.StreamHandler(sys.stdout)
        format_str = (
            format_str or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(logging.Formatter(format_str))
        handlers = [handler]

    # Add all handlers
    for handler in handlers:
        root_logger.addHandler(handler)


__all__ = [
    "configure_logging",
    "logger",
]
