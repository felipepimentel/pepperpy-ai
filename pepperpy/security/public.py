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

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Set


# Authentication classes
class AuthProvider:
    """Base class for authentication providers."""

    def __init__(self, name: str):
        """Initialize the auth provider.

        Args:
            name: Provider name

        """
        self.name = name


class Authenticator:
    """Authentication service."""

    def __init__(self, provider: AuthProvider):
        """Initialize the authenticator.

        Args:
            provider: Authentication provider

        """
        self.provider = provider


# Content security classes
class ContentFilter:
    """Base class for content filtering."""

    def __init__(self, name: str):
        """Initialize the content filter.

        Args:
            name: Filter name

        """
        self.name = name


class PromptProtection:
    """Protection against prompt injection attacks."""

    def __init__(self, filters: Optional[Set[ContentFilter]] = None):
        """Initialize prompt protection.

        Args:
            filters: Content filters to use

        """
        self.filters = filters or set()


# Audit classes
@dataclass
class AuditEvent:
    """Base class for audit events."""

    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = field(default_factory=dict)


class AuditLogger:
    """Logging for security events."""

    def __init__(self, name: str):
        """Initialize the audit logger.

        Args:
            name: Logger name

        """
        self.name = name

    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event.

        Args:
            event: Event to log

        """


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
