"""JSON formatter for structured logging.

This module provides a JSON formatter for structured logging output.
"""

import json
import logging
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
            exception=self.formatException(record.exc_info) if record.exc_info else None,
        )

        # Convert to JSON
        return json.dumps(log_record.model_dump(), default=str)


# Export public API
__all__ = [
    "JsonFormatter",
    "LogRecord",
]