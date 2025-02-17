"""Monitoring module for logging, metrics, and tracing."""

import logging as python_logging
import sys
from typing import Any, Dict, Optional

from .logging import LogLevel, LogRecord, get_logger, setup_logging
from .metrics import MetricsManager, metrics_manager
from .tracing import Span, SpanContext, TracingManager

# Configure root logger
python_logging.basicConfig(
    level=python_logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Create logger for this module
logger = python_logging.getLogger("pepperpy")


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
    log_level = getattr(python_logging, level.upper())
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
        "level": getattr(python_logging, level.upper()),
        "format": format,
    }

    if filename:
        config["filename"] = filename
    else:
        config["stream"] = sys.stdout

    python_logging.basicConfig(**config)


__all__ = [
    "LogLevel",
    "LogRecord",
    "MetricsManager",
    "Span",
    "SpanContext",
    "TracingManager",
    "configure_logging",
    "get_logger",
    "log_event",
    "logger",
    "metrics_manager",
    "setup_logging",
]
