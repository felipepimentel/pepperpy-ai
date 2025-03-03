"""Type definitions for security providers.

This module defines common types used by security providers.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class SecuritySeverity(Enum):
    """Severity levels for security issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityCategory(Enum):
    """Categories of security issues."""

    INJECTION = "injection"
    SENSITIVE_DATA = "sensitive_data"
    MALICIOUS_CONTENT = "malicious_content"
    POLICY_VIOLATION = "policy_violation"
    OTHER = "other"


class SecurityIssue:
    """Representation of a security issue."""

    def __init__(
        self,
        issue_id: str,
        category: SecurityCategory,
        severity: SecuritySeverity,
        description: str,
        content_span: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize security issue.

        Args:
            issue_id: Unique identifier for the issue
            category: Category of the issue
            severity: Severity level
            description: Description of the issue
            content_span: Optional span in the content (start, end)
            metadata: Optional additional metadata

        """
        self.issue_id = issue_id
        self.category = category
        self.severity = severity
        self.description = description
        self.content_span = content_span or {}
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation

        """
        return {
            "issue_id": self.issue_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "content_span": self.content_span,
            "metadata": self.metadata,
        }


class SecurityValidationResult:
    """Result of a security validation."""

    def __init__(
        self,
        is_valid: bool,
        issues: Optional[List[SecurityIssue]] = None,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize validation result.

        Args:
            is_valid: Whether the content is valid
            issues: List of security issues
            score: Optional security score (0-1, higher is more secure)
            metadata: Optional additional metadata

        """
        self.is_valid = is_valid
        self.issues = issues or []
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation

        """
        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
            "score": self.score,
            "metadata": self.metadata,
        }
