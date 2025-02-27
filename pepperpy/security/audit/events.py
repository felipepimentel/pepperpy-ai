"""Audit events functionality for PepperPy security.

This module provides functionality for tracking and recording security-relevant
events and actions within PepperPy.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AuditEventType(Enum):
    """Types of audit events."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    DATA_ACCESS = "data_access"
    SYSTEM_CHANGE = "system_change"
    SECURITY_ALERT = "security_alert"


class AuditEventSeverity(Enum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Container for audit event information."""

    event_type: AuditEventType
    timestamp: datetime = field(default_factory=datetime.now)
    severity: AuditEventSeverity = AuditEventSeverity.INFO
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    action: str = ""
    status: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """Logger for security audit events."""

    def __init__(self):
        self._events: List[AuditEvent] = []

    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event."""
        self._events.append(event)

    def get_events(
        self,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditEventSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AuditEvent]:
        """Get filtered audit events."""
        filtered_events = self._events

        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        if severity:
            filtered_events = [e for e in filtered_events if e.severity == severity]
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]

        return filtered_events

    def clear_events(self) -> None:
        """Clear all recorded audit events."""
        self._events.clear()
