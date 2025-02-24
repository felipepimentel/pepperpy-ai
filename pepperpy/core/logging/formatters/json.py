"""
JSON formatter for log records.
"""

import json
from typing import Any

from pepperpy.core.logging.base import LogFormatter
from pepperpy.core.logging.types import LogRecord


class JsonFormatter(LogFormatter):
    """Formats log records as JSON."""

    def __init__(self, indent: int = None, sort_keys: bool = False):
        self.indent = indent
        self.sort_keys = sort_keys

    def _serialize_record(self, record: LogRecord) -> dict[str, Any]:
        """Convert a log record to a serializable dictionary."""
        data = {
            "timestamp": record.timestamp.isoformat(),
            "level": str(record.level),
            "message": record.message,
            "logger": record.logger_name,
        }

        if record.module:
            data["module"] = record.module

        if record.function:
            data["function"] = record.function

        if record.line_number is not None:
            data["line_number"] = record.line_number

        if record.context:
            data["context"] = record.context

        if record.exception_info:
            data["exception"] = {
                "type": record.exception_info.__class__.__name__,
                "message": str(record.exception_info),
            }

        if record.stack_info:
            data["stack_info"] = record.stack_info

        return data

    def format(self, record: LogRecord) -> str:
        """Format a log record as JSON."""
        data = self._serialize_record(record)
        return json.dumps(
            data,
            indent=self.indent,
            sort_keys=self.sort_keys,
            default=str,
        )
