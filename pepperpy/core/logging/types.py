"""
Types and enums for the logging system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def __str__(self) -> str:
        return self.value

    @property
    def numeric_value(self) -> int:
        """Get the numeric value of the log level."""
        return {
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARNING: 30,
            LogLevel.ERROR: 40,
            LogLevel.CRITICAL: 50,
        }[self]


@dataclass
class LogRecord:
    """Represents a log record."""

    level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: dict[str, Any] = field(default_factory=dict)
    logger_name: str = "root"
    module: str | None = None
    function: str | None = None
    line_number: int | None = None
    exception_info: Exception | None = None
    stack_info: str | None = None


@dataclass
class LogConfig:
    """Configuration for the logging system."""

    default_level: LogLevel = LogLevel.INFO
    handlers: dict[str, dict[str, Any]] = field(default_factory=dict)
    formatters: dict[str, dict[str, Any]] = field(default_factory=dict)
    filters: dict[str, dict[str, Any]] = field(default_factory=dict)
    loggers: dict[str, dict[str, Any]] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    propagate: bool = True
    capture_stack: bool = False
    capture_locals: bool = False
