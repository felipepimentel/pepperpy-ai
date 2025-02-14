"""Error classes for Pepperpy capabilities.

This module defines error classes specific to different capability types
like learning, planning, and reasoning.
"""

from typing import Any

from pepperpy.core.errors import ErrorCategory, ErrorContext, PepperpyError


class CapabilityError(PepperpyError):
    """Base class for capability-related errors."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize capability error.

        Args:
            message: Error message
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        super().__init__(
            message,
            category=ErrorCategory.RUNTIME,
            error_code="CAP001",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class LearningError(CapabilityError):
    """Error raised by learning capabilities."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize learning error.

        Args:
            message: Error message
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class PlanningError(CapabilityError):
    """Error raised by planning capabilities."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize planning error.

        Args:
            message: Error message
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class ReasoningError(CapabilityError):
    """Error raised by reasoning capabilities."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize reasoning error.

        Args:
            message: Error message
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )
