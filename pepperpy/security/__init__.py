"""Security package for PepperPy.

This package provides security-related functionality including:
- Audit logging and event tracking
- Access control and authorization
- Secure configuration management
- Threat detection and prevention
- Content filtering and prompt protection
"""

# Re-export public interfaces
from pepperpy.security.public import (
    AuditEvent,
    AuditLogger,
    Authenticator,
    AuthProvider,
    ContentFilter,
    PromptProtection,
)

# Internal implementations
from .content import (  # Content filtering; Prompt protection
    ContentCategory,
    ContentGuard,
    ContentPolicy,
    ContentRule,
    DetectionResult,
    FilterMatch,
    FilterResult,
    InjectionPattern,
    PersonalInfoDetector,
    PromptGuard,
    PromptSanitizer,
    PromptValidator,
    ThreatLevel,
)

__all__ = [
    # Public interfaces
    "AuthProvider",
    "Authenticator",
    "ContentFilter",
    "PromptProtection",
    "AuditLogger",
    "AuditEvent",
    # Internal implementations
    # Content filtering
    "ContentCategory",
    "ContentRule",
    "FilterMatch",
    "FilterResult",
    "PersonalInfoDetector",
    "ContentPolicy",
    "ContentGuard",
    # Prompt protection
    "ThreatLevel",
    "InjectionPattern",
    "DetectionResult",
    "PromptSanitizer",
    "PromptValidator",
    "PromptGuard",
]
