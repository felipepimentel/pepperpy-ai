"""Memory-related error definitions."""

from typing import Any

from pepperpy.core.errors import PepperError


class MemoryError(PepperError):
    """Base class for memory-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize memory error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "MEM000"
        super().__init__(message, details=error_details)


class MemoryKeyError(MemoryError):
    """Raised when a memory key operation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize memory key error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "MEM001"
        super().__init__(message, details=error_details)


class MemoryTypeError(MemoryError):
    """Raised when a memory type operation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize memory type error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "MEM002"
        super().__init__(message, details=error_details)


class MemoryStorageError(MemoryError):
    """Error raised when a memory storage operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize memory storage error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "MEM003"
        super().__init__(message, details=error_details)


class MemoryQueryError(MemoryError):
    """Error raised when a memory query is invalid or fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize memory query error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "MEM004"
        super().__init__(message, details=error_details)


class MemoryInitError(MemoryError):
    """Error raised when memory initialization fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize memory initialization error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "MEM005"
        super().__init__(message, details=error_details)


class MemoryCleanupError(MemoryError):
    """Error raised when memory cleanup fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize memory cleanup error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "MEM006"
        super().__init__(message, details=error_details)
