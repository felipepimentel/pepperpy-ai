"""@file: logging.py
@purpose: Core logging functionality for the Pepperpy framework
@component: Core
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import logging
import sys
from typing import Any, Dict, Optional, Union

# Configure root logger
root_logger = logging.getLogger("pepperpy")
root_logger.setLevel(logging.INFO)

# Add default console handler if none exists
if not root_logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name

    Returns:
        Logger instance

    """
    return logging.getLogger(f"pepperpy.{name}")


def set_log_level(level: Union[str, int]) -> None:
    """Set the global log level.

    Args:
        level: Log level to set

    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    root_logger.setLevel(level)


def configure_logging(
    level: Union[str, int] = logging.INFO,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
    handlers: Optional[Dict[str, Any]] = None,
) -> None:
    """Configure logging system.

    Args:
        level: Log level
        format_string: Log format string
        date_format: Date format string
        handlers: Additional handlers configuration

    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    root_logger.setLevel(level)

    # Configure format
    format_string = format_string or "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = date_format or "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(format_string, datefmt=date_format)

    # Update existing handlers
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

    # Add additional handlers
    if handlers:
        for handler_type, config in handlers.items():
            if handler_type == "file":
                handler = logging.FileHandler(config["filename"])
                handler.setFormatter(formatter)
                root_logger.addHandler(handler)
            # Add more handler types as needed
