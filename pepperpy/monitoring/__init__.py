"""Monitoring module for metrics, health checks, tracing, and audit logging.

This module provides comprehensive monitoring capabilities including:
- Metrics collection and reporting
- Health checks
- Distributed tracing
- Audit logging
"""

import logging
from pathlib import Path

# Configure base logger
logger = logging.getLogger("pepperpy")
logger.setLevel(logging.INFO)

# Create logs directory
log_dir = Path.home() / ".pepperpy/logs"
log_dir.mkdir(parents=True, exist_ok=True)

# Create file handler
log_file = log_dir / "pepperpy.log"
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

# Import submodules
from pepperpy.monitoring.audit import AuditLogger, audit_logger
from pepperpy.monitoring.health import HealthManager
from pepperpy.monitoring.metrics.simple import MetricsManager

__all__ = [
    "logger",
    "AuditLogger",
    "audit_logger",
    "MetricsManager",
    "HealthManager",
]
