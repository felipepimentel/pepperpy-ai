"""Memory-related errors."""

from typing import Any, Dict, Optional

from pepperpy.core.errors import ErrorContext, PepperpyError


class MemoryError(PepperpyError):
    """Base class for memory-related errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize memory error.

        Args:
            message: Error message
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for error recovery
            context: Error context

        """
        super().__init__(
            message=message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class MemoryKeyError(MemoryError):
    """Error raised when a memory key is invalid or not found."""

    pass


class MemoryTypeError(MemoryError):
    """Error raised when a memory type is invalid or not supported."""

    pass


class MemoryStorageError(MemoryError):
    """Error raised when memory storage operations fail."""

    pass


class MemoryQueryError(MemoryError):
    """Error raised when memory query operations fail."""

    pass
