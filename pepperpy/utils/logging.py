"""Logging utilities for PepperPy.

This module provides logging utilities for the PepperPy framework.
"""

import logging
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: The name of the logger
        level: The log level (defaults to INFO if not specified)

    Returns:
        The logger instance
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    else:
        logger.setLevel(logging.INFO)

    # Only add a handler if the logger doesn't already have one
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
