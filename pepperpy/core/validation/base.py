"""Base interfaces and exceptions for validation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar

T = TypeVar("T")


class ValidationError(Exception):
    """Base exception for validation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize validation error.

        Args:
            message: Error message
            details: Optional error details

        """
        super().__init__(message)
        self.details = details or {}


class Validator(ABC):
    """Base class for all validators."""

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate a value.

        Args:
            value: Value to validate

        Returns:
            bool: True if value is valid, False otherwise

        """

    def __call__(self, value: Any) -> bool:
        """Make validator callable.

        Args:
            value: Value to validate

        Returns:
            bool: True if value is valid, False otherwise

        """
        return self.validate(value)
