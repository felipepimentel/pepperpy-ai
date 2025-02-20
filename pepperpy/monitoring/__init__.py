"""Monitoring module for Pepperpy.

This module provides monitoring functionality, including:
- Logging configuration
- Metrics collection
- Tracing utilities
- Audit logging
"""

import logging
import os
from pathlib import Path

# Configure root logger
logger = logging.getLogger("pepperpy")
logger.setLevel(logging.INFO)

# Create formatters
console_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Create file handler if log directory exists
log_dir = Path.home() / ".pepperpy/logs"
if not log_dir.exists():
    try:
        log_dir.mkdir(parents=True)
        file_handler = logging.FileHandler(log_dir / "pepperpy.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Failed to create log directory: {e}")

# Import audit logger
from pepperpy.monitoring.audit import audit_logger

__all__ = ["logger", "audit_logger"]
