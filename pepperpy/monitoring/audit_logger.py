"""Audit logging for security events.

This module provides secure audit logging capabilities for tracking security-relevant
events in the system.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

# Configure audit logger
audit_logger = logging.getLogger("pepperpy.audit")
audit_logger.setLevel(logging.INFO)

# Add secure file handler
_file_handler = logging.FileHandler("audit.log")
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
audit_logger.addHandler(_file_handler)


async def log(
    event: Dict[str, Any],
    level: int = logging.INFO,
    user: Optional[str] = None,
) -> None:
    """Log an audit event securely.

    Args:
        event: Event data to log
        level: Log level (default: INFO)
        user: Optional user identifier
    """
    # Add metadata
    event["timestamp"] = event.get("timestamp", datetime.utcnow().isoformat())
    if user:
        event["user"] = user

    # Log event
    audit_logger.log(level, json.dumps(event))
