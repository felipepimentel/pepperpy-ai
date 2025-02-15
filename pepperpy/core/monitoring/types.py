"""Core monitoring types.

This module defines the core types and enums used across the monitoring system.
"""

from enum import Enum
from typing import Any, Dict, Optional

__all__ = [
    "LogLevel",
    "MetricType",
    "MonitoringError",
]


class LogLevel(Enum):
    """Standard log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics supported by the system."""

    COUNTER = "counter"  # Monotonically increasing value
    GAUGE = "gauge"  # Value that can go up and down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Statistical distribution


class MonitoringError(Exception):
    """Base class for monitoring errors."""

    def __init__(
        self,
        message: str,
        error_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            error_type: Type of error
            details: Additional error details

        """
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
