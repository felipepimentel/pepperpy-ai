"""Security package for PepperPy.

This package provides security-related functionality including:
- Audit logging and event tracking
- Access control and authorization
- Secure configuration management
- Threat detection and prevention
- Content filtering and prompt protection
"""

from .audit import (
    AuditEvent,
    AuditEventSeverity,
    AuditEventType,
    AuditLogger,
)
from .content import (
    # Content filtering
    ContentCategory,
    ContentFilter,
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
    # Prompt protection
    ThreatLevel,
)

__all__ = [
    # Audit
    "AuditEvent",
    "AuditEventType",
    "AuditEventSeverity",
    "AuditLogger",
    # Content filtering
    "ContentCategory",
    "ContentRule",
    "FilterMatch",
    "FilterResult",
    "ContentFilter",
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
