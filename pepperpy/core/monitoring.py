"""Monitoring and observability module for Pepperpy.

This module provides centralized logging, metrics tracking, and tracing
capabilities for the Pepperpy system. It follows a structured logging
approach with context-aware loggers and tracers.
"""

import logging
import sys
from typing import cast

from structlog import BoundLogger, wrap_logger
from structlog import get_logger as get_structlog_logger
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    format_exc_info,
)
from structlog.stdlib import LoggerFactory, add_log_level
from structlog.types import Processor as ProcessorType


def _get_processor_chain() -> list[ProcessorType]:
    """Get the processor chain for structured logging.

    Returns:
        list[ProcessorType]: List of structlog processors in the order they
        should be applied.

    Example:
        >>> processors = _get_processor_chain()
        >>> assert len(processors) == 5
        >>> assert any(isinstance(p, JSONRenderer) for p in processors)
    """
    return [
        format_exc_info,
        StackInfoRenderer(),
        TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=True),
        add_log_level,
        JSONRenderer(),
    ]


def _configure_logging() -> None:
    """Configure the logging system.

    This function sets up basic logging configuration with:
    - Output format for structured logging
    - Standard output stream
    - INFO log level

    Example:
        >>> _configure_logging()
        >>> logger = logging.getLogger()
        >>> assert logger.level == logging.INFO
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name: str | None = None) -> BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Optional name for the logger. If not provided, uses the
            module name.

    Returns:
        BoundLogger: A structured logger instance configured with the
        standard processor chain.

    Example:
        >>> logger = get_logger("test")
        >>> logger.info("test message", key="value")  # Outputs JSON
        >>> assert isinstance(logger, BoundLogger)
    """
    _configure_logging()
    base_logger = get_structlog_logger(name)
    return cast(
        BoundLogger,
        wrap_logger(
            base_logger,
            processors=_get_processor_chain(),
            logger_factory=LoggerFactory(),
        ),
    )


# Create the default logger instance
logger = get_logger("pepperpy")
