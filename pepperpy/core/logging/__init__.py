"""Structured logging system for PepperPy core

This module provides a structured logging system for the PepperPy core,
enabling consistent, configurable logging across the entire framework.

Classes:
    Logger: Base logger interface
    StructuredLogger: Logger implementation with structured output
    LogLevel: Enum of log levels
    LogHandler: Base class for log handlers

Functions:
    get_logger: Get a logger instance for a specific module
    configure_logging: Configure global logging settings
"""

from pepperpy.core.logging.base import (
    Logger,
    LogHandler,
    LogLevel,
    StructuredLogger,
    configure_logging,
    get_logger,
)

__all__ = [
    "LogHandler",
    "LogLevel",
    "Logger",
    "StructuredLogger",
    "configure_logging",
    "get_logger",
]
