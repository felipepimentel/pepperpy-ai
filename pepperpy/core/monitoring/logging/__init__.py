"""Logging module for structured logging with context."""

from .errors import LoggingError
from .factory import Logger, LoggerFactory
from .types import LogLevel, LogRecord

# Global logger factory instance
logger_manager = LoggerFactory()


def get_logger(name: str) -> Logger:
    """Get a logger by name.

    Args:
        name: Logger name

    Returns:
        Logger instance

    """
    return logger_manager.get_logger(name)


def setup_logging(
    default_level: LogLevel = LogLevel.INFO,
    default_context: dict[str, str] | None = None,
    default_metadata: dict[str, str] | None = None,
) -> None:
    """Set up logging configuration.

    Args:
        default_level: Default log level
        default_context: Default context for all loggers
        default_metadata: Default metadata for all loggers

    """
    logger_manager.configure(
        default_level=default_level,
        default_context=default_context,
        default_metadata=default_metadata,
    )


__all__ = [
    "LoggerFactory",
    "LogLevel",
    "LogRecord",
    "LoggingError",
    "get_logger",
    "logger_manager",
    "setup_logging",
]
