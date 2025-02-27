"""Audit package for PepperPy security.

This package provides functionality for security auditing, including event
tracking, logging, analysis, and reporting of security-relevant actions.
"""

from .analyzer import AuditAnalyzer
from .events import (
    AuditEvent,
    AuditEventSeverity,
    AuditEventType,
    AuditLogger,
)
from .reporting import AuditReport

__all__ = [
    # Event types and data structures
    "AuditEvent",
    "AuditEventType",
    "AuditEventSeverity",
    # Core functionality
    "AuditLogger",
    # Analysis
    "AuditAnalyzer",
    # Reporting
    "AuditReport",
]
