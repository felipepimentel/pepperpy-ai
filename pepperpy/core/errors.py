"""Error classes for PepperPy.

This module provides error classes used throughout the PepperPy framework.
"""

from typing import Any, Optional


class PepperpyError(Exception):
    """Base class for all PepperPy exceptions.

    All custom exceptions in PepperPy should inherit from this class.
    """

    def __init__(self, message: str, *args, **kwargs):
        """Initialize a PepperPy error.

        Args:
            message: Error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(message, *args)
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            Error message
        """
        return self.message


class ProviderError(PepperpyError):
    """Error raised by providers during initialization or execution."""


class ValidationError(PepperpyError):
    """Error raised when validation fails.

    This error is used when validating input parameters, configuration,
    or data structures.

    Args:
        message: Error message
        field: Name of the field that failed validation
        rule: Name of the validation rule that failed
        value: Value that failed validation
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        rule: Optional[str] = None,
        value: Optional[Any] = None,
        *args,
        **kwargs
    ):
        """Initialize a validation error.

        Args:
            message: Error message
            field: Name of the field that failed validation
            rule: Name of the validation rule that failed
            value: Value that failed validation
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(message, *args, **kwargs)
        self.field = field
        self.rule = rule
        self.value = value

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            Formatted error message with field and rule information
        """
        parts = [self.message]
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.rule:
            parts.append(f"Rule: {self.rule}")
        if self.value is not None:
            parts.append(f"Value: {self.value}")
        return " | ".join(parts)


class ConfigurationError(PepperpyError):
    """Raised when configuration is invalid or missing."""
    pass
