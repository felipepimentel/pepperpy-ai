"""Memory-specific error types."""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class MemoryError(PepperpyError):
    """Base error class for memory operations."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory error.

        Args:
            message: Error message
            code: Optional error code
            details: Optional error details
        """
        error_details = {"error_code": code or "MEM001", **(details or {})}
        super().__init__(message, code=code, details=error_details)


class MemoryKeyError(MemoryError):
    """Error raised when a memory key is invalid or not found."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory key error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, code="MEM002", details=details)


class MemoryTypeError(MemoryError):
    """Error raised when a memory type is invalid or not supported."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory type error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, code="MEM003", details=details)


class MemoryStorageError(MemoryError):
    """Error raised when a memory storage operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory storage error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, code="MEM004", details=details)


class MemoryQueryError(MemoryError):
    """Error raised when a memory query is invalid or fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory query error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, code="MEM005", details=details)


class MemoryInitError(MemoryError):
    """Error raised when memory initialization fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory initialization error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, code="MEM006", details=details)


class MemoryCleanupError(MemoryError):
    """Error raised when memory cleanup fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory cleanup error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, code="MEM007", details=details)
