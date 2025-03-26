"""Validation utilities for PepperPy.

This module provides utilities for validating configuration, input data,
and other aspects of the framework.

Example:
    >>> from pepperpy.core.validation import validate_config
    >>> config = {"api_key": "abc123"}
    >>> validate_config(config, required=["api_key"])
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pepperpy.core.base import ValidationError

T = TypeVar("T")


def validate_config(
    config: Dict[str, Any],
    required_fields: Optional[List[str]] = None,
    optional_fields: Optional[List[str]] = None,
) -> None:
    """Validate configuration dictionary.

    Args:
        config: Configuration dictionary to validate
        required_fields: List of required field names
        optional_fields: List of optional field names

    Raises:
        ValidationError: If validation fails
    """
    if required_fields:
        missing = [f for f in required_fields if f not in config]
        if missing:
            raise ValidationError(
                f"Missing required configuration fields: {', '.join(missing)}"
            )

    if optional_fields:
        allowed_fields = set(required_fields or []) | set(optional_fields)
        unknown = [f for f in config if f not in allowed_fields]
        if unknown:
            raise ValidationError(f"Unknown configuration fields: {', '.join(unknown)}")


def validate_type(
    value: Any,
    expected_type: Union[Type[T], List[Type[T]]],
    field_name: str = "value",
) -> None:
    """Validate that a value is of the expected type.

    Args:
        value: Value to validate
        expected_type: Expected type or list of types
        field_name: Name of the field being validated

    Raises:
        ValidationError: If validation fails
    """
    if isinstance(expected_type, list):
        if not any(isinstance(value, t) for t in expected_type):
            raise ValidationError(
                f"Invalid type for {field_name}. Expected one of: "
                f"{[t.__name__ for t in expected_type]}, got: {type(value).__name__}"
            )
    elif not isinstance(value, expected_type):
        raise ValidationError(
            f"Invalid type for {field_name}. "
            f"Expected {expected_type.__name__}, got: {type(value).__name__}"
        )


def validate_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    field_name: str = "value",
) -> None:
    """Validate that a numeric value is within a range.

    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        field_name: Name of the field being validated

    Raises:
        ValidationError: If validation fails
    """
    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Invalid value for {field_name}. "
            f"Must be greater than or equal to {min_value}"
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"Invalid value for {field_name}. Must be less than or equal to {max_value}"
        )


def validate_length(
    value: Union[str, List[Any], Dict[Any, Any]],
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = "value",
) -> None:
    """Validate that a value's length is within a range.

    Args:
        value: Value to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        field_name: Name of the field being validated

    Raises:
        ValidationError: If validation fails
    """
    length = len(value)

    if min_length is not None and length < min_length:
        raise ValidationError(
            f"Invalid length for {field_name}. Must be at least {min_length} characters"
        )

    if max_length is not None and length > max_length:
        raise ValidationError(
            f"Invalid length for {field_name}. Must be at most {max_length} characters"
        )


def validate_pattern(
    value: str,
    pattern: str,
    field_name: str = "value",
) -> None:
    """Validate that a string matches a pattern.

    Args:
        value: String to validate
        pattern: Regular expression pattern
        field_name: Name of the field being validated

    Raises:
        ValidationError: If validation fails
    """
    import re

    if not re.match(pattern, value):
        raise ValidationError(
            f"Invalid format for {field_name}. Must match pattern: {pattern}"
        )


def validate_options(
    value: Any,
    options: List[Any],
    field_name: str = "value",
) -> None:
    """Validate that a value is one of the allowed options.

    Args:
        value: Value to validate
        options: List of allowed options
        field_name: Name of the field being validated

    Raises:
        ValidationError: If validation fails
    """
    if value not in options:
        raise ValidationError(
            f"Invalid value for {field_name}. "
            f"Must be one of: {', '.join(str(o) for o in options)}"
        )


def validate_path(path: Union[str, "Path"]) -> None:
    """Validate file path.

    Args:
        path: Path to validate

    Raises:
        ValidationError: If path validation fails

    Example:
        >>> validate_path("/tmp/config.yaml")
        >>> validate_path(Path("/tmp/data.json"))
    """
    from pathlib import Path

    try:
        path = Path(path)
    except Exception as e:
        raise ValidationError(
            f"Invalid path: {e}",
            field="path",
            rule="format",
            value=str(path),
        )


__all__ = [
    "validate_config",
    "validate_type",
    "validate_range",
    "validate_length",
    "validate_pattern",
    "validate_options",
    "validate_path",
]
