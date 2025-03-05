"""Validation protocols for PepperPy.

This module defines protocols for validation of objects and data
in the PepperPy framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union

T = TypeVar("T")  # Validated type


class ValidationResult:
    """Result of a validation operation.

    Attributes:
        valid: Whether the validation passed
        errors: List of validation errors
        warnings: List of validation warnings
    """

    def __init__(
        self,
        valid: bool = True,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        """Initialize the validation result.

        Args:
            valid: Whether the validation passed
            errors: List of validation errors
            warnings: List of validation warnings
        """
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str) -> None:
        """Add a validation error.

        Args:
            error: Error message
        """
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: str) -> None:
        """Add a validation warning.

        Args:
            warning: Warning message
        """
        self.warnings.append(warning)

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one.

        Args:
            other: Validation result to merge
        """
        self.valid = self.valid and other.valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def __bool__(self) -> bool:
        """Convert to boolean.

        Returns:
            True if valid, False otherwise
        """
        return self.valid

    def __str__(self) -> str:
        """Convert to string.

        Returns:
            String representation of the validation result
        """
        if self.valid:
            if self.warnings:
                return f"Valid with {len(self.warnings)} warnings"
            return "Valid"
        return f"Invalid with {len(self.errors)} errors"


class Validatable(Protocol):
    """Protocol for validatable objects.

    Validatable objects can be validated to ensure they meet
    certain criteria.
    """

    def validate(self) -> ValidationResult:
        """Validate the object.

        Returns:
            Validation result
        """
        ...


class Validator(ABC):
    """Abstract base class for validators.

    Validators check if objects or data meet certain criteria.
    """

    @abstractmethod
    def validate(self, obj: Any) -> ValidationResult:
        """Validate an object.

        Args:
            obj: Object to validate

        Returns:
            Validation result
        """
        pass


class SchemaValidator(Validator):
    """Validator that validates objects against a schema.

    This validator checks if objects conform to a specified schema.
    """

    def __init__(self, schema: Dict[str, Any]):
        """Initialize the schema validator.

        Args:
            schema: Schema to validate against
        """
        self.schema = schema

    def validate(self, obj: Any) -> ValidationResult:
        """Validate an object against the schema.

        Args:
            obj: Object to validate

        Returns:
            Validation result
        """
        result = ValidationResult()

        # Simple implementation that checks if required fields are present
        if not isinstance(obj, dict):
            result.add_error("Object must be a dictionary")
            return result

        for field, field_schema in self.schema.items():
            # Check if required field is present
            if field_schema.get("required", False) and field not in obj:
                result.add_error(f"Required field '{field}' is missing")

            # Check field type if present
            if field in obj and "type" in field_schema:
                expected_type = field_schema["type"]
                value = obj[field]

                if expected_type == "string" and not isinstance(value, str):
                    result.add_error(f"Field '{field}' must be a string")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    result.add_error(f"Field '{field}' must be a number")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    result.add_error(f"Field '{field}' must be a boolean")
                elif expected_type == "array" and not isinstance(value, list):
                    result.add_error(f"Field '{field}' must be an array")
                elif expected_type == "object" and not isinstance(value, dict):
                    result.add_error(f"Field '{field}' must be an object")

        return result


class CompositeValidator(Validator):
    """Validator that combines multiple validators.

    This validator applies multiple validators to an object and
    combines their results.
    """

    def __init__(self, validators: Optional[List[Validator]] = None):
        """Initialize the composite validator.

        Args:
            validators: List of validators to apply
        """
        self.validators = validators or []

    def add_validator(self, validator: Validator) -> None:
        """Add a validator.

        Args:
            validator: Validator to add
        """
        self.validators.append(validator)

    def validate(self, obj: Any) -> ValidationResult:
        """Validate an object using all validators.

        Args:
            obj: Object to validate

        Returns:
            Combined validation result
        """
        result = ValidationResult()

        for validator in self.validators:
            validator_result = validator.validate(obj)
            result.merge(validator_result)

        return result
