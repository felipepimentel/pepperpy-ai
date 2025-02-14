"""Type definitions for logging."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class LogLevel(Enum):
    """Log levels in order of severity."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogRecord:
    """A structured log record.

    This class represents a single log entry with context and metadata.

    Attributes:
        level: Log level
        message: Log message
        timestamp: When the log was created
        module: Module that created the log
        context: Contextual information
        metadata: Additional metadata
        error: Optional error information

    """

    level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    module: str = "root"
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert log record to dictionary.

        Returns:
            Dictionary representation of the log record

        """
        data = {
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "module": self.module,
            "context": self.context,
            "metadata": self.metadata,
        }

        if self.error:
            data["error"] = {
                "type": self.error.__class__.__name__,
                "message": str(self.error),
            }

        return data
