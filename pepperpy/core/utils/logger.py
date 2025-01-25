"""Logging system for Pepperpy framework."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .constants import LogLevel, DEFAULT_LOG_DIR

# Configure default logging format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class PepperpyLogger:
    """Custom logger for Pepperpy framework."""
    
    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        log_file: Optional[str] = None,
        format_str: Optional[str] = None,
        date_format: Optional[str] = None
    ):
        """Initialize logger.
        
        Args:
            name: Logger name
            level: Log level
            log_file: Optional log file path
            format_str: Optional log format string
            date_format: Optional date format string
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level.value)
        
        # Create formatters
        formatter = logging.Formatter(
            format_str or DEFAULT_FORMAT,
            date_format or DEFAULT_DATE_FORMAT
        )
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            file_handler = self._setup_file_handler(log_file, formatter)
            self.logger.addHandler(file_handler)
    
    def _setup_file_handler(
        self,
        log_file: str,
        formatter: logging.Formatter
    ) -> logging.FileHandler:
        """Set up file handler.
        
        Args:
            log_file: Log file path
            formatter: Log formatter
            
        Returns:
            Configured file handler.
        """
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create and configure file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        return file_handler
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message.
        
        Args:
            msg: Message to log
            **kwargs: Additional logging context
        """
        self.logger.debug(msg, extra=kwargs)
    
    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message.
        
        Args:
            msg: Message to log
            **kwargs: Additional logging context
        """
        self.logger.info(msg, extra=kwargs)
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message.
        
        Args:
            msg: Message to log
            **kwargs: Additional logging context
        """
        self.logger.warning(msg, extra=kwargs)
    
    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message.
        
        Args:
            msg: Message to log
            **kwargs: Additional logging context
        """
        self.logger.error(msg, extra=kwargs)
    
    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log critical message.
        
        Args:
            msg: Message to log
            **kwargs: Additional logging context
        """
        self.logger.critical(msg, extra=kwargs)

# Global logger cache
_loggers: Dict[str, PepperpyLogger] = {}

def get_logger(
    name: str,
    level: LogLevel = LogLevel.INFO,
    log_file: Optional[str] = None
) -> PepperpyLogger:
    """Get or create a logger instance.
    
    Args:
        name: Logger name
        level: Log level
        log_file: Optional log file path
        
    Returns:
        Logger instance.
    """
    if name not in _loggers:
        # Generate default log file path if not provided
        if not log_file:
            log_dir = os.path.expanduser(DEFAULT_LOG_DIR)
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
        
        _loggers[name] = PepperpyLogger(name, level, log_file)
    
    return _loggers[name] 