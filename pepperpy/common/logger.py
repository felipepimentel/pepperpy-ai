"""Structured logging functionality."""

import logging
import sys
from typing import Any, Dict, Optional

from pepperpy.common.errors import PepperpyError


class LoggingError(PepperpyError):
    """Logging error."""
    pass


def setup_logging(
    level: int = logging.INFO,
    format_str: Optional[str] = None,
    filename: Optional[str] = None,
) -> None:
    """Set up logging configuration.
    
    Args:
        level: Logging level
        format_str: Optional log format string
        filename: Optional log file path
        
    Raises:
        LoggingError: If setup fails
    """
    try:
        if format_str is None:
            format_str = (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            
        handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(format_str))
        handlers.append(console_handler)
        
        # File handler if filename provided
        if filename:
            file_handler = logging.FileHandler(filename)
            file_handler.setFormatter(logging.Formatter(format_str))
            handlers.append(file_handler)
            
        # Configure root logger
        logging.basicConfig(
            level=level,
            format=format_str,
            handlers=handlers,
            force=True,
        )
    except Exception as e:
        raise LoggingError(f"Failed to set up logging: {str(e)}")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class StructuredLogger:
    """Structured logger with context support."""
    
    def __init__(self, name: str):
        """Initialize logger.
        
        Args:
            name: Logger name
        """
        self._logger = get_logger(name)
        self._context: Dict[str, Any] = {}
        
    def add_context(self, **kwargs: Any) -> None:
        """Add context data.
        
        Args:
            **kwargs: Context key-value pairs
        """
        self._context.update(kwargs)
        
    def clear_context(self) -> None:
        """Clear context data."""
        self._context.clear()
        
    def _format_message(self, message: str) -> str:
        """Format message with context.
        
        Args:
            message: Message to format
            
        Returns:
            Formatted message
        """
        if not self._context:
            return message
            
        context_str = " ".join(
            f"{k}={v}" for k, v in sorted(self._context.items())
        )
        return f"{message} [{context_str}]"
        
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        with_context = dict(self._context)
        with_context.update(kwargs)
        self._logger.debug(self._format_message(message), extra=with_context)
        
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        with_context = dict(self._context)
        with_context.update(kwargs)
        self._logger.info(self._format_message(message), extra=with_context)
        
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        with_context = dict(self._context)
        with_context.update(kwargs)
        self._logger.warning(self._format_message(message), extra=with_context)
        
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        with_context = dict(self._context)
        with_context.update(kwargs)
        self._logger.error(self._format_message(message), extra=with_context)
        
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        with_context = dict(self._context)
        with_context.update(kwargs)
        self._logger.critical(self._format_message(message), extra=with_context)


__all__ = [
    "LoggingError",
    "setup_logging",
    "get_logger",
    "StructuredLogger",
] 