"""Utility functions for validation."""

from typing import Any, Type, TypeVar

T = TypeVar("T")


def validate_type(value: Any, expected_type: Type[T]) -> T:
    """Validate that a value is of the expected type.

    Args:
        value: The value to validate.
        expected_type: The expected type.

    Returns:
        The validated value.

    Raises:
        TypeError: If the value is not of the expected type.
    """
    if not isinstance(value, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")
    return value 