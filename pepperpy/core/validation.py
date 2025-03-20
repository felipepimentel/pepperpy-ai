"""Validation Module.

This module provides validation utilities for the PepperPy framework,
including configuration validation, input validation, and error handling.

Example:
    >>> from pepperpy.core.validation import validate_config
    >>> config = {"api_key": "abc123"}
    >>> validate_config(config, required=["api_key"])
"""

from typing import Any, Dict, List, Optional, Union


class ValidationError(Exception):
    """Error raised when validation fails.

    This error includes details about which field failed validation
    and what validation rule was violated.

    Args:
        message: Error message
        field: Field that failed validation
        rule: Validation rule that was violated
        details: Additional error details

    Example:
        >>> raise ValidationError(
        ...     "Invalid API key",
        ...     field="api_key",
        ...     rule="format"
        ... )
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        rule: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            rule: Validation rule that was violated
            details: Additional error details
        """
        super().__init__(message)
        self.field = field
        self.rule = rule
        self.details = details or {}


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


def validate_type(
    value: Any,
    expected_type: Union[type, tuple[type, ...]],
    field: str,
) -> None:
    """Validate value type.

    Args:
        value: Value to validate
        expected_type: Expected type(s)
        field: Field name for error reporting

    Raises:
        ValidationError: If validation fails

    Example:
        >>> validate_type("abc123", str, "api_key")
        >>> validate_type(42, (int, float), "timeout")
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Invalid type for {field}: expected {expected_type}, got {type(value)}",
            field=field,
            rule="type",
            details={
                "expected": str(expected_type),
                "actual": str(type(value)),
            },
        )


def validate_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    field: str = "",
) -> None:
    """Validate numeric range.

    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        field: Field name for error reporting

    Raises:
        ValidationError: If validation fails

    Example:
        >>> validate_range(0.7, min_value=0.0, max_value=1.0, field="temperature")
        >>> validate_range(42, min_value=0, field="timeout")
    """
    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Value for {field} must be >= {min_value}",
            field=field,
            rule="min_value",
            details={"min_value": min_value, "value": value},
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"Value for {field} must be <= {max_value}",
            field=field,
            rule="max_value",
            details={"max_value": max_value, "value": value},
        )


def validate_pattern(
    value: str,
    pattern: str,
    field: str = "",
) -> None:
    """Validate string pattern.

    Args:
        value: Value to validate
        pattern: Regular expression pattern
        field: Field name for error reporting

    Raises:
        ValidationError: If validation fails

    Example:
        >>> validate_pattern("abc123", r"^[a-z0-9]+$", "username")
    """
    import re

    if not re.match(pattern, value):
        raise ValidationError(
            f"Invalid format for {field}",
            field=field,
            rule="pattern",
            details={"pattern": pattern, "value": value},
        )


def validate_path(
    path: Union[str, "Path"],
    must_exist: bool = True,
    create_parents: bool = False,
    field: str = "",
) -> None:
    """Validate file system path.

    Args:
        path: Path to validate
        must_exist: Whether path must exist
        create_parents: Whether to create parent directories
        field: Field name for error reporting

    Raises:
        ValidationError: If validation fails

    Example:
        >>> validate_path("/path/to/file", must_exist=False, create_parents=True)
    """
    from pathlib import Path

    try:
        path_obj = Path(path) if isinstance(path, str) else path
        if create_parents:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        if must_exist and not path_obj.exists():
            raise ValidationError(
                f"Path does not exist: {path_obj}",
                field=field,
                rule="exists",
            )
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(
            f"Invalid path: {str(e)}",
            field=field,
            rule="path",
            details={"error": str(e)},
        )


class ValidationSchema:
    """Schema for validation.

    This class provides a way to define validation rules for data structures.
    It supports type checking, required fields, and custom validation rules.

    Args:
        schema: Schema definition

    Example:
        >>> schema = ValidationSchema({
        ...     "name": {"type": str, "required": True},
        ...     "age": {"type": int, "min": 0},
        ...     "email": {"type": str, "pattern": r"^[^@]+@[^@]+\.[^@]+$"}
        ... })
        >>> data = schema.validate({"name": "Alice", "age": 30})
    """

    def __init__(self, schema: Dict[str, Any]):
        """Initialize the validation schema.

        Args:
            schema: Schema definition

        Raises:
            ValidationError: If schema is invalid
        """
        if not isinstance(schema, dict):
            raise ValidationError(
                "Schema must be a dictionary",
                field="schema",
                rule="type",
            )
        self.schema = schema

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema.

        Args:
            data: Data to validate

        Returns:
            Validated data with defaults applied

        Raises:
            ValidationError: If validation fails

        Example:
            >>> schema = ValidationSchema({
            ...     "name": {"type": str, "required": True},
            ...     "age": {"type": int, "default": 0}
            ... })
            >>> validated = schema.validate({"name": "Alice"})
            >>> print(validated["age"])  # 0
        """
        if not isinstance(data, dict):
            raise ValidationError(
                "Data must be a dictionary",
                field="data",
                rule="type",
            )

        result = {}

        # Check required fields and apply defaults
        for field, rules in self.schema.items():
            if field in data:
                value = data[field]
            elif "default" in rules:
                value = rules["default"]
            elif rules.get("required", False):
                raise ValidationError(
                    f"Missing required field: {field}",
                    field=field,
                    rule="required",
                )
            else:
                continue

            # Validate type
            if "type" in rules:
                validate_type(value, rules["type"], field)

            # Validate range
            if isinstance(value, (int, float)):
                validate_range(
                    value,
                    min_value=rules.get("min"),
                    max_value=rules.get("max"),
                    field=field,
                )

            # Validate pattern
            if isinstance(value, str) and "pattern" in rules:
                validate_pattern(value, rules["pattern"], field)

            result[field] = value

        # Check for unknown fields
        unknown_fields = set(data.keys()) - set(self.schema.keys())
        if unknown_fields:
            raise ValidationError(
                f"Unknown fields: {', '.join(unknown_fields)}",
                field="data",
                rule="unknown_fields",
                details={"fields": list(unknown_fields)},
            )

        return result

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            String representation of schema

        Example:
            >>> schema = ValidationSchema({"name": {"type": str}})
            >>> str(schema)  # "ValidationSchema(fields=1)"
        """
        return f"ValidationSchema(fields={len(self.schema)})"

    def __repr__(self) -> str:
        """Get detailed string representation.

        Returns:
            Detailed string representation of schema

        Example:
            >>> schema = ValidationSchema({"name": {"type": str}})
            >>> repr(schema)  # Contains full schema definition
        """
        return f"{self.__class__.__name__}(schema={self.schema})"


__all__ = [
    "ValidationError",
    "ValidationSchema",
    "validate_config",
    "validate_type",
    "validate_range",
    "validate_pattern",
    "validate_path",
]
