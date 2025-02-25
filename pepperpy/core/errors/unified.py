"""Unified error classes for the Pepperpy framework.

This module provides the base error classes used throughout the framework.
"""

from typing import Any


class PepperpyError(Exception):
    """Base class for all Pepperpy errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        recovery_hint: str | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            details: Optional error details
            recovery_hint: Optional hint for error recovery
        """
        super().__init__(message)
        self.details = details or {}
        self.recovery_hint = recovery_hint


class RegistryError(PepperpyError):
    """Error raised when a registry operation fails."""
