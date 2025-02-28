"""Logging formatters for the Pepperpy framework.

This package provides various logging formatters for structured logging output
in different formats like JSON.
"""

from pepperpy.monitoring.logging.formatters.json import JsonFormatter

__all__ = ["JsonFormatter"]
"""JSON formatter for structured logging.

This module provides a JSON formatter for structured logging output.
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pepperpy.core.models import BaseModel, Field


class LogRecord(BaseModel):
    """Log record model.

    Attributes:
        timestamp: Log timestamp
        level: Log level
        logger: Logger name
        message: Log message
        context: Log context
        exception: Exception if any
    """

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str
    logger: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)
    exception: str | None = None


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    This formatter converts log records to JSON format for structured logging.
    It includes standard fields like timestamp, level, logger name, message,
    as well as additional context and exception information if available.

    Example:
        >>> import logging
        >>> logger = logging.getLogger("test")
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(JsonFormatter())
        >>> logger.addHandler(handler)
        >>> logger.info("Test message", extra={"context": {"key": "value"}})
        {"timestamp": "2024-02-15T12:34:56.789Z", "level": "INFO", "logger": "test",
         "message": "Test message", "context": {"key": "value"}, "exception": null}
    """

    def __init__(
        self,
        indent: int | None = None,
        sort_keys: bool = False,
        default: Callable[[Any], Any] | None = None,
        encoders: dict[type, Callable[[Any], Any]] | None = None,
    ) -> None:
        """Initialize JSON formatter.

        Args:
            indent: Optional JSON indentation
            sort_keys: Whether to sort dictionary keys
            default: Default JSON encoder function
            encoders: Custom type encoders
        """
        super().__init__()
        self.indent = indent
        self.sort_keys = sort_keys
        self.default = default or str
        self.encoders = encoders or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string representation of the log record
        """
        # Extract context from record
        context = getattr(record, "context", {})
        if not isinstance(context, dict):
            context = {}

        # Create log record
        log_record = LogRecord(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            context=context,
            exception=self.formatException(record.exc_info)
            if record.exc_info
            else None,
        )

        # Convert to JSON
        return json.dumps(
            log_record.model_dump(),
            indent=self.indent,
            sort_keys=self.sort_keys,
            default=self._encode_value,
        )

    def _encode_value(self, obj: Any) -> Any:
        """Encode value using custom encoders.

        Args:
            obj: Value to encode

        Returns:
            JSON-serializable value
        """
        # Try custom encoders first
        for type_, encoder in self.encoders.items():
            if isinstance(obj, type_):
                return encoder(obj)

        # Fall back to default encoder
        return self.default(obj)


# Export public API
__all__ = [
    "JsonFormatter",
    "LogRecord",
]
"""@file: text.py
@purpose: Text log formatter implementation
@component: Core/Logging
@created: 2024-02-25
@task: TASK-007-R020
@status: completed
"""
