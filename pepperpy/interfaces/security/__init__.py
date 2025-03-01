"""Public Interface for security

This module provides a stable public interface for the security functionality.
It exposes the core security abstractions and implementations that are
considered part of the public API.

Authentication:
    AuthProvider: Base class for authentication providers
    Authenticator: Authentication service

Content Security:
    ContentFilter: Base class for content filtering
    PromptProtection: Protection against prompt injection attacks

Audit:
    AuditLogger: Logging for security events
    AuditEvent: Base class for audit events
"""

# Import public classes and functions from the implementation
from pepperpy.security.auth import AuthProvider, Authenticator
from pepperpy.security.content.filter import ContentFilter
from pepperpy.security.content.prompt_protection import PromptProtection
from pepperpy.security.audit.events import AuditEvent
from pepperpy.security.audit.logger import AuditLogger

__all__ = [
    # Authentication
    "AuthProvider",
    "Authenticator",
    # Content Security
    "ContentFilter",
    "PromptProtection",
    # Audit
    "AuditLogger",
    "AuditEvent",
] 