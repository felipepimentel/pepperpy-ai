"""@file: logging.py
@purpose: Core logging functionality for the Pepperpy framework
@component: Core
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import logging
from typing import Union

from pepperpy.monitoring import configure_logging


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: Union[str, int]) -> None:
    """Set the global log level.

    Args:
        level: Log level to set
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    logging.getLogger().setLevel(level)


__all__ = ["get_logger", "set_log_level", "configure_logging"]
