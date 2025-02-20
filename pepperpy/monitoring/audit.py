"""Audit logging for security events.

This module provides audit logging functionality for security-relevant events.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from pepperpy.monitoring import logger as base_logger

# Configure audit logger
logger = base_logger.getChild("audit")

# Create audit log directory
audit_log_dir = Path.home() / ".pepperpy/logs/audit"
audit_log_dir.mkdir(parents=True, exist_ok=True)

# Create audit file handler
audit_file = audit_log_dir / "audit.log"
audit_handler = logging.FileHandler(audit_file)
audit_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(audit_handler)


class AuditLogger:
    """Audit logger for security events."""

    def __init__(self) -> None:
        """Initialize the audit logger."""
        self.logger = logger

    async def log(self, event: Dict[str, Any]) -> None:
        """Log a security event.

        Args:
            event: Event data to log. Must include:
                - event_type: Type of event
                - timestamp: Event timestamp
                Additional fields are allowed.
        """
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().isoformat()

        self.logger.info(
            "Security event",
            extra={
                "event": json.dumps(event),
            },
        )


# Global audit logger instance
audit_logger = AuditLogger()

__all__ = ["audit_logger"]
