"""Monitoring module for Pepperpy.

This module provides logging, metrics, and tracing capabilities.
"""

import logging
import sys
from typing import Any, Dict, Optional

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Create logger for this module
logger = logging.getLogger("pepperpy")


def log_event(
    event: str,
    level: str = "INFO",
    **kwargs: Any,
) -> None:
    """Log an event with additional context.

    Args:
        event: Event description
        level: Log level
        **kwargs: Additional context

    """
    log_level = getattr(logging, level.upper())
    logger.log(log_level, event, extra=kwargs)


def configure_logging(
    level: str = "INFO",
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename: Optional[str] = None,
) -> None:
    """Configure logging settings.

    Args:
        level: Log level
        format: Log format
        filename: Optional log file

    """
    config: Dict[str, Any] = {
        "level": getattr(logging, level.upper()),
        "format": format,
    }

    if filename:
        config["filename"] = filename
    else:
        config["stream"] = sys.stdout

    logging.basicConfig(**config)
