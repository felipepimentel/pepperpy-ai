"""Audit package for PepperPy security.

This package provides functionality for security auditing, including event
tracking, logging, and analysis of security-relevant actions.
"""

from .events import (
    AuditEvent,
    AuditEventSeverity,
    AuditEventType,
    AuditLogger,
)

__all__ = [
    "AuditEvent",
    "AuditEventType",
    "AuditEventSeverity",
    "AuditLogger",
]
