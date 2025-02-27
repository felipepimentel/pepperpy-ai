"""Security package for PepperPy.

This package provides security-related functionality including:
- Audit logging and event tracking
- Access control and authorization
- Secure configuration management
- Threat detection and prevention
"""

from .audit import (
    AuditEvent,
    AuditEventSeverity,
    AuditEventType,
    AuditLogger,
)

__all__ = [
    # Audit
    "AuditEvent",
    "AuditEventType",
    "AuditEventSeverity",
    "AuditLogger",
]
