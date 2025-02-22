"""Audit logging for security events.

This module provides secure audit logging capabilities for tracking security-relevant
events in the system.
"""

from pepperpy.monitoring.audit.logger import AuditLogger, audit_logger

__all__ = ["AuditLogger", "audit_logger"]
