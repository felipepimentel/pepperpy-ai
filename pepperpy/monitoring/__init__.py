"""Monitoring package for logging and observability.

This package provides logging and monitoring functionality for the Pepperpy library.
"""

from typing import Any

from pepperpy.monitoring.logger import get_logger
from pepperpy.monitoring.metrics import metrics

# Create a logger instance
logger = get_logger("pepperpy")


def bind_logger(**kwargs: Any) -> Any:
    """Create a new logger with bound context.

    Args:
    ----
        **kwargs: Context variables to bind

    Returns:
    -------
        A new logger instance with bound context

    """
    return logger.bind(**kwargs)


__all__ = ["logger", "bind_logger", "metrics"]
