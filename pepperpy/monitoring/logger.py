"""Logger module for Pepperpy.

This module provides logging utilities and configuration.
"""

import logging
import sys
from typing import Any, Dict, Optional

from pepperpy.monitoring import logger as base_logger


class StructuredLogger:
    """Structured logger for Pepperpy."""

    def __init__(self, name: str) -> None:
        """Initialize the structured logger.

        Args:
            name: Logger name
        """
        self._logger = base_logger.getChild(name)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            message: Message to log
            **kwargs: Additional fields to log
        """
        self._logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            message: Message to log
            **kwargs: Additional fields to log
        """
        self._logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: Message to log
            **kwargs: Additional fields to log
        """
        self._logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: Message to log
            **kwargs: Additional fields to log
        """
        self._logger.debug(message, extra=kwargs)


class LoggerFactory:
    """Factory for creating loggers."""

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger instance.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        return base_logger.getChild(name)

    @staticmethod
    def get_structured_logger(name: str) -> StructuredLogger:
        """Get a structured logger instance.

        Args:
            name: Logger name

        Returns:
            Structured logger instance
        """
        return StructuredLogger(name)


class LoggerManager:
    """Manager for configuring loggers."""

    def __init__(self) -> None:
        """Initialize the logger manager."""
        self._loggers: Dict[str, logging.Logger] = {}

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        if name not in self._loggers:
            self._loggers[name] = LoggerFactory.get_logger(name)
        return self._loggers[name]

    def configure(
        self,
        level: int = logging.INFO,
        format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers: Optional[list[logging.Handler]] = None,
    ) -> None:
        """Configure logging.

        Args:
            level: Logging level
            format: Log format
            handlers: Optional list of handlers
        """
        base_logger.setLevel(level)

        if not base_logger.handlers:
            if handlers:
                for handler in handlers:
                    base_logger.addHandler(handler)
            else:
                handler = logging.StreamHandler(sys.stdout)
                handler.setLevel(level)
                formatter = logging.Formatter(format)
                handler.setFormatter(formatter)
                base_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return LoggerFactory.get_logger(name)


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name

    Returns:
        Structured logger instance
    """
    return LoggerFactory.get_structured_logger(name)


# Create a default structured logger
structured_logger = get_structured_logger("pepperpy")
