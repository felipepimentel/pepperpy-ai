"""@file: logging.py
@purpose: Core logging functionality for the Pepperpy framework
@component: Core
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import logging

from pepperpy.monitoring.logging import (
    LogLevel,
    get_logger,
)
from pepperpy.monitoring.logging.base import configure_logging


def set_log_level(level: str | int) -> None:
    """Set the global log level.

    Args:
        level: Log level to set (string or integer)
    """
    if isinstance(level, str):
        level = LogLevel.from_str(level)
    logging.getLogger().setLevel(level)


__all__ = ["configure_logging", "get_logger", "set_log_level"]
