"""Monitoring module for logging, metrics, and tracing."""

import logging as python_logging
import sys
from typing import Any, Dict, Optional

from pepperpy.monitoring.logger import (
    LoggerFactory,
    LoggerManager,
    StructuredLogger,
    get_logger,
    get_structured_logger,
    structured_logger,
)
from pepperpy.monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    Metric,
    MetricType,
    MetricsRegistry,
)

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
    "LoggerFactory",
    "LoggerManager",
    "StructuredLogger",
    "Counter",
    "Gauge",
    "Histogram",
    "Metric",
    "MetricType",
    "MetricsRegistry",
    "configure_logging",
    "get_logger",
    "get_structured_logger",
    "log_event",
    "logger",
    "structured_logger",
]
