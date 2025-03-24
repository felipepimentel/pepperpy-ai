"""Validation Module.

This module provides validation utilities for the PepperPy framework,
including configuration validation, input validation, and error handling.

Example:
    >>> from pepperpy.core.validation import validate_config
    >>> config = {"api_key": "abc123"}
    >>> validate_config(config, required=["api_key"])
"""

from typing import Any, Dict, List, Optional, Union

from pepperpy.core.base import ValidationError


def validate_config(
    config: Dict[str, Any],
    required: Optional[List[str]] = None,
    optional: Optional[List[str]] = None,
) -> None:
    """Validate configuration dictionary.

    Args:
        config: Configuration to validate
        required: List of required fields
        optional: List of optional fields

    Raises:
        ValidationError: If validation fails

    Example:
        >>> config = {"api_key": "abc123", "timeout": 30}
        >>> validate_config(
        ...     config,
        ...     required=["api_key"],
        ...     optional=["timeout"]
        ... )
    """
    if not isinstance(config, dict):
        raise ValidationError(
            "Configuration must be a dictionary",
            field="config",
            rule="type",
        )

    # Check required fields
    if required:
        for field in required:
            if field not in config:
                raise ValidationError(
                    f"Missing required field: {field}",
                    field=field,
                    rule="required",
                )

    # Check for unknown fields
    if optional:
        allowed_fields = set(required or []) | set(optional)
        unknown_fields = set(config.keys()) - allowed_fields
        if unknown_fields:
            raise ValidationError(
                f"Unknown fields: {', '.join(unknown_fields)}",
                field="config",
                rule="unknown_fields",
                details={"fields": list(unknown_fields)},
            )


def validate_type(value: Any, expected_type: type) -> None:
    """Validate value type.

    Args:
        value: Value to validate
        expected_type: Expected type

    Raises:
        ValidationError: If type validation fails

    Example:
        >>> validate_type("test", str)
        >>> validate_type(123, int)
        >>> validate_type({"key": "value"}, dict)
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Expected type {expected_type.__name__}, got {type(value).__name__}",
            field="value",
            rule="type",
            value=value,
        )


def validate_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
) -> None:
    """Validate numeric value range.

    Args:
        value: Value to validate
        min_value: Optional minimum value (inclusive)
        max_value: Optional maximum value (inclusive)

    Raises:
        ValidationError: If range validation fails

    Example:
        >>> validate_range(5, min_value=0, max_value=10)
        >>> validate_range(3.14, min_value=0)
        >>> validate_range(-1, max_value=0)
    """
    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Value {value} is less than minimum {min_value}",
            field="value",
            rule="min_value",
            value=value,
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"Value {value} is greater than maximum {max_value}",
            field="value",
            rule="max_value",
            value=value,
        )


def validate_pattern(value: str, pattern: str) -> None:
    """Validate string pattern.

    Args:
        value: String to validate
        pattern: Regular expression pattern

    Raises:
        ValidationError: If pattern validation fails

    Example:
        >>> validate_pattern("test@example.com", r"^[^@]+@[^@]+\.[^@]+$")
        >>> validate_pattern("123-456", r"^\d{3}-\d{3}$")
    """
    import re

    if not re.match(pattern, value):
        raise ValidationError(
            f"Value does not match pattern: {pattern}",
            field="value",
            rule="pattern",
            value=value,
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
    "validate_pattern",
    "validate_path",
]
