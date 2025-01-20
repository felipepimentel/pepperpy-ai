"""Logging utilities for Pepperpy."""

import logging
import sys
from pathlib import Path
from typing import Optional, Union

from ..config import LoggingConfig


def setup_logging(
    level: Union[str, int] = "INFO",
    format_str: Optional[str] = None,
    output_path: Optional[Union[str, Path]] = None
) -> None:
    """Set up logging configuration.
    
    Args:
        level: Logging level (default: INFO)
        format_str: Log format string
        output_path: Optional path for log file
        
    Raises:
        ValueError: If level is invalid
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), None)
        if not isinstance(level, int):
            raise ValueError(f"Invalid log level: {level}")
            
    # Set default format if none provided
    if not format_str:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if output path provided
    if output_path:
        if isinstance(output_path, str):
            output_path = Path(output_path)
            
        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(output_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def setup_logging_from_config(config: LoggingConfig) -> None:
    """Set up logging from configuration.
    
    Args:
        config: Logging configuration
    """
    setup_logging(
        level=config.level,
        format_str=config.format,
        output_path=config.output_path
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name) 