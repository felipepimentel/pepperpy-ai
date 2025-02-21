"""Security-related error types."""

from typing import Any, Dict, Optional


class SecurityError(Exception):
    """Base class for security-related errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(SecurityError):
    """Error raised when validation fails."""

    pass
