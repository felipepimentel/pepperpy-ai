#!/usr/bin/env python
"""
Formatters for logging.

This module provides formatters for structured logging.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

# pip install pydantic
try:
    from pydantic import BaseModel, Field
except ImportError:
    print("Pydantic not installed. Install with: pip install pydantic")
    BaseModel = object

    def Field(*args, **kwargs):
        def decorator(x):
            return x

        return decorator


class LogRecord(BaseModel):
    """Model for structured log records."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str
    logger: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    exception: Optional[str] = None


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    This formatter converts log records to JSON format for structured logging.
    It includes timestamp, level, logger name, message, and any additional context.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the log record

        """
        # Extract exception info if present
        exception = None
        if record.exc_info:
            exception = self.formatException(record.exc_info)

        # Create structured log record
        log_record = LogRecord(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            context=getattr(record, "context", {}),
            exception=exception,
        )

        # Convert to JSON
        return json.dumps(log_record.model_dump(), default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output.

    This formatter adds color to log messages based on their level.
    """

    COLORS = {
        "DEBUG": "\x1B[36m",  # Cyan
        "INFO": "\x1B[32m",  # Green
        "WARNING": "\x1B[33m",  # Yellow
        "ERROR": "\x1B[31m",  # Red
        "CRITICAL": "\x1B[41m\x1B[37m",  # White on Red background
    }
    RESET = "\x1B[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors.

        Args:
            record: The log record to format

        Returns:
            Colored string representation of the log record

        """
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{log_message}{self.RESET}"
