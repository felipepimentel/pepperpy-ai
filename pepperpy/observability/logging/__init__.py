"""Structured logging for PepperPy.

This module provides structured logging capabilities for the PepperPy framework:
- Context-aware logging: Include context information in log entries
- Structured output: Generate structured log data for easier analysis
- Log levels: Support different log levels for filtering
- Log routing: Route logs to different destinations

The logging system enables applications to generate meaningful and structured logs
that facilitate debugging, monitoring, and analysis of system behavior.
"""

import logging

# Export public API
__all__ = [
    "get_logger",
]


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance

    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
