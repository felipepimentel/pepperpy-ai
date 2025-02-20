"""Core monitoring functionality for Pepperpy.

This package provides monitoring capabilities including:
- Metrics collection and reporting
- Logging configuration and management
- Tracing and distributed tracing
"""

import logging
from typing import Optional

from pepperpy.monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricExporter,
    MetricsManager,
    MetricType,
    MetricUnit,
)

logger = logging.getLogger(__name__)


def configure_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """Configure logging for the framework.

    Args:
        level: Optional log level (default: INFO)
        log_file: Optional log file path
    """
    if level is None:
        level = "INFO"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Add console handler if not already present
    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root_logger.addHandler(file_handler)

    logger.info(
        "Logging configured",
        extra={
            "level": level,
            "log_file": log_file,
        },
    )


__all__ = [
    "configure_logging",
    "Counter",
    "Gauge",
    "Histogram",
    "MetricExporter",
    "MetricsManager",
    "MetricType",
    "MetricUnit",
]
