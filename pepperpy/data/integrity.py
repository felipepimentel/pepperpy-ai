"""Data consistency and integrity validation.

This module provides functionality for validating data consistency and integrity,
including integrity checks, consistency validators, and validation hooks for data
operations. It integrates with the validation framework to provide comprehensive
data validation capabilities.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from pepperpy.data.errors import ValidationError
from pepperpy.data.validation import (
    ValidationHook,
    ValidationLevel,
    ValidationResult,
    ValidationStage,
    Validator,
    register_validator,
)
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables for data types
T = TypeVar("T")
U = TypeVar("U")


class IntegrityCheckType(Enum):
    """Type of integrity check.

    This enum defines the type of integrity check to perform.
    """

    # Check for referential integrity (e.g., foreign key constraints)
    REFERENTIAL = "referential"
    # Check for uniqueness constraints
    UNIQUENESS = "uniqueness"
    # Check for data type constraints
    TYPE = "type"
    # Check for value range constraints
    RANGE = "range"
    # Check for format constraints
    FORMAT = "format"
    # Check for custom business rules
    BUSINESS_RULE = "business_rule"
    # Check for data consistency across related entities
    CROSS_ENTITY = "cross_entity"
    # Check for temporal consistency (e.g., start date before end date)
    TEMPORAL = "temporal"
    # Check for data completeness
    COMPLETENESS = "completeness"


class IntegrityCheck(ABC):
    """Base class for integrity checks.

    Integrity checks are responsible for validating specific aspects of data integrity.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the integrity check.

        Returns:
            The name of the integrity check
        """
        pass

    @property
    @abstractmethod
    def check_type(self) -> IntegrityCheckType:
        """Get the type of integrity check.

        Returns:
            The type of integrity check
        """
        pass

    @abstractmethod
    def check(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check data integrity.

        Args:
            data: The data to check
            context: Additional context for the check, or None if not needed

        Returns:
            The validation result
        """
        pass


class FunctionIntegrityCheck(IntegrityCheck):
    """Integrity check that uses a function.

    This integrity check uses a function to check data integrity.
    """

    def __init__(
        self,
        name: str,
        check_type: IntegrityCheckType,
        func: Callable[[Any, Optional[Dict[str, Any]]], ValidationResult],
    ):
        """Initialize a function integrity check.

        Args:
            name: The name of the integrity check
            check_type: The type of integrity check
            func: The integrity check function
        """
        self._name = name
        self._check_type = check_type
        self._func = func

    @property
    def name(self) -> str:
        """Get the name of the integrity check.

        Returns:
            The name of the integrity check
        """
        return self._name

    @property
    def check_type(self) -> IntegrityCheckType:
        """Get the type of integrity check.

        Returns:
            The type of integrity check
        """
        return self._check_type

    def check(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check data integrity.

        Args:
            data: The data to check
            context: Additional context for the check, or None if not needed

        Returns:
            The validation result
        """
        return self._func(data, context)


class ReferentialIntegrityCheck(IntegrityCheck):
    """Integrity check for referential integrity.

    This integrity check validates that references to other entities are valid.
    """

    def __init__(
        self,
        name: str,
        source_field: str,
        target_entity: str,
        target_field: str,
        resolver: Callable[[Any, str], bool],
    ):
        """Initialize a referential integrity check.

        Args:
            name: The name of the integrity check
            source_field: The field in the source entity that contains the reference
            target_entity: The name of the target entity
            target_field: The field in the target entity that is referenced
            resolver: A function that checks if a reference exists in the target entity
        """
        self._name = name
        self._source_field = source_field
        self._target_entity = target_entity
        self._target_field = target_field
        self._resolver = resolver

    @property
    def name(self) -> str:
        """Get the name of the integrity check.

        Returns:
            The name of the integrity check
        """
        return self._name

    @property
    def check_type(self) -> IntegrityCheckType:
        """Get the type of integrity check.

        Returns:
            The type of integrity check
        """
        return IntegrityCheckType.REFERENTIAL

    def check(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check data integrity.

        Args:
            data: The data to check
            context: Additional context for the check, or None if not needed

        Returns:
            The validation result
        """
        # Extract the reference value from the source entity
        if not isinstance(data, dict):
            return ValidationResult(
                False,
                errors={
                    "referential_integrity": f"Expected dictionary, got {type(data).__name__}"
                },
            )

        if self._source_field not in data:
            return ValidationResult(
                False,
                errors={
                    "referential_integrity": f"Source field '{self._source_field}' not found in data"
                },
            )

        reference_value = data[self._source_field]
        if reference_value is None:
            # Null references are allowed
            return ValidationResult(True, data=data)

        # Check if the reference exists in the target entity
        if not self._resolver(reference_value, self._target_entity):
            return ValidationResult(
                False,
                errors={
                    "referential_integrity": f"Reference to {self._target_entity}.{self._target_field} with value '{reference_value}' does not exist"
                },
            )

        return ValidationResult(True, data=data)


class UniquenessCheck(IntegrityCheck):
    """Integrity check for uniqueness constraints.

    This integrity check validates that values in specified fields are unique.
    """

    def __init__(
        self,
        name: str,
        fields: Union[str, List[str]],
        resolver: Callable[[Any, Union[str, List[str]]], bool],
    ):
        """Initialize a uniqueness check.

        Args:
            name: The name of the integrity check
            fields: The field or fields that must have unique values
            resolver: A function that checks if values are unique
        """
        self._name = name
        self._fields = fields if isinstance(fields, list) else [fields]
        self._resolver = resolver

    @property
    def name(self) -> str:
        """Get the name of the integrity check.

        Returns:
            The name of the integrity check
        """
        return self._name

    @property
    def check_type(self) -> IntegrityCheckType:
        """Get the type of integrity check.

        Returns:
            The type of integrity check
        """
        return IntegrityCheckType.UNIQUENESS

    def check(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check data integrity.

        Args:
            data: The data to check
            context: Additional context for the check, or None if not needed

        Returns:
            The validation result
        """
        # Extract the values from the data
        if not isinstance(data, dict):
            return ValidationResult(
                False,
                errors={
                    "uniqueness": f"Expected dictionary, got {type(data).__name__}"
                },
            )

        # Check if all fields exist in the data
        missing_fields = [field for field in self._fields if field not in data]
        if missing_fields:
            return ValidationResult(
                False,
                errors={
                    "uniqueness": f"Fields {', '.join(missing_fields)} not found in data"
                },
            )

        # Check if the values are unique
        if not self._resolver(data, self._fields):
            field_str = ", ".join(self._fields)
            values = [data[field] for field in self._fields]
            value_str = ", ".join(str(value) for value in values)
            return ValidationResult(
                False,
                errors={
                    "uniqueness": f"Values for fields {field_str} with values {value_str} are not unique"
                },
            )

        return ValidationResult(True, data=data)


class RangeCheck(IntegrityCheck):
    """Integrity check for value range constraints.

    This integrity check validates that values in specified fields are within a valid range.
    """

    def __init__(
        self,
        name: str,
        field: str,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None,
        inclusive_min: bool = True,
        inclusive_max: bool = True,
    ):
        """Initialize a range check.

        Args:
            name: The name of the integrity check
            field: The field to check
            min_value: The minimum allowed value, or None for no minimum
            max_value: The maximum allowed value, or None for no maximum
            inclusive_min: Whether the minimum value is inclusive
            inclusive_max: Whether the maximum value is inclusive
        """
        self._name = name
        self._field = field
        self._min_value = min_value
        self._max_value = max_value
        self._inclusive_min = inclusive_min
        self._inclusive_max = inclusive_max

    @property
    def name(self) -> str:
        """Get the name of the integrity check.

        Returns:
            The name of the integrity check
        """
        return self._name

    @property
    def check_type(self) -> IntegrityCheckType:
        """Get the type of integrity check.

        Returns:
            The type of integrity check
        """
        return IntegrityCheckType.RANGE

    def check(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check data integrity.

        Args:
            data: The data to check
            context: Additional context for the check, or None if not needed

        Returns:
            The validation result
        """
        # Extract the value from the data
        if not isinstance(data, dict):
            return ValidationResult(
                False,
                errors={"range": f"Expected dictionary, got {type(data).__name__}"},
            )

        if self._field not in data:
            return ValidationResult(
                False,
                errors={"range": f"Field '{self._field}' not found in data"},
            )

        value = data[self._field]
        if value is None:
            # Null values are allowed
            return ValidationResult(True, data=data)

        # Check if the value is within the valid range
        if self._min_value is not None:
            if self._inclusive_min:
                if value < self._min_value:
                    return ValidationResult(
                        False,
                        errors={
                            "range": f"Value {value} for field '{self._field}' is less than minimum {self._min_value}"
                        },
                    )
            else:
                if value <= self._min_value:
                    return ValidationResult(
                        False,
                        errors={
                            "range": f"Value {value} for field '{self._field}' is less than or equal to minimum {self._min_value}"
                        },
                    )

        if self._max_value is not None:
            if self._inclusive_max:
                if value > self._max_value:
                    return ValidationResult(
                        False,
                        errors={
                            "range": f"Value {value} for field '{self._field}' is greater than maximum {self._max_value}"
                        },
                    )
            else:
                if value >= self._max_value:
                    return ValidationResult(
                        False,
                        errors={
                            "range": f"Value {value} for field '{self._field}' is greater than or equal to maximum {self._max_value}"
                        },
                    )

        return ValidationResult(True, data=data)


class FormatCheck(IntegrityCheck):
    """Integrity check for format constraints.

    This integrity check validates that values in specified fields match a specified format.
    """

    def __init__(
        self,
        name: str,
        field: str,
        format_validator: Callable[[Any], bool],
        error_message: str,
    ):
        """Initialize a format check.

        Args:
            name: The name of the integrity check
            field: The field to check
            format_validator: A function that checks if a value matches the required format
            error_message: The error message to use if validation fails
        """
        self._name = name
        self._field = field
        self._format_validator = format_validator
        self._error_message = error_message

    @property
    def name(self) -> str:
        """Get the name of the integrity check.

        Returns:
            The name of the integrity check
        """
        return self._name

    @property
    def check_type(self) -> IntegrityCheckType:
        """Get the type of integrity check.

        Returns:
            The type of integrity check
        """
        return IntegrityCheckType.FORMAT

    def check(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check data integrity.

        Args:
            data: The data to check
            context: Additional context for the check, or None if not needed

        Returns:
            The validation result
        """
        # Extract the value from the data
        if not isinstance(data, dict):
            return ValidationResult(
                False,
                errors={"format": f"Expected dictionary, got {type(data).__name__}"},
            )

        if self._field not in data:
            return ValidationResult(
                False,
                errors={"format": f"Field '{self._field}' not found in data"},
            )

        value = data[self._field]
        if value is None:
            # Null values are allowed
            return ValidationResult(True, data=data)

        # Check if the value matches the required format
        if not self._format_validator(value):
            return ValidationResult(
                False,
                errors={"format": f"{self._error_message}: {value}"},
            )

        return ValidationResult(True, data=data)


class CompletenessCheck(IntegrityCheck):
    """Integrity check for data completeness.

    This integrity check validates that required fields are present and non-null.
    """

    def __init__(
        self,
        name: str,
        required_fields: List[str],
        allow_empty: bool = False,
    ):
        """Initialize a completeness check.

        Args:
            name: The name of the integrity check
            required_fields: The fields that are required
            allow_empty: Whether empty values (empty strings, empty lists, etc.) are allowed
        """
        self._name = name
        self._required_fields = required_fields
        self._allow_empty = allow_empty

    @property
    def name(self) -> str:
        """Get the name of the integrity check.

        Returns:
            The name of the integrity check
        """
        return self._name

    @property
    def check_type(self) -> IntegrityCheckType:
        """Get the type of integrity check.

        Returns:
            The type of integrity check
        """
        return IntegrityCheckType.COMPLETENESS

    def check(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check data integrity.

        Args:
            data: The data to check
            context: Additional context for the check, or None if not needed

        Returns:
            The validation result
        """
        # Check if the data is a dictionary
        if not isinstance(data, dict):
            return ValidationResult(
                False,
                errors={
                    "completeness": f"Expected dictionary, got {type(data).__name__}"
                },
            )

        # Check if all required fields are present and non-null
        missing_fields = []
        empty_fields = []

        for field in self._required_fields:
            if field not in data:
                missing_fields.append(field)
            elif data[field] is None:
                missing_fields.append(field)
            elif not self._allow_empty:
                # Check for empty values
                value = data[field]
                if (isinstance(value, str) and not value) or (
                    isinstance(value, (list, dict, set)) and not value
                ):
                    empty_fields.append(field)

        errors = {}
        if missing_fields:
            errors["missing_fields"] = (
                f"Required fields are missing or null: {', '.join(missing_fields)}"
            )
        if empty_fields:
            errors["empty_fields"] = (
                f"Required fields are empty: {', '.join(empty_fields)}"
            )

        if errors:
            return ValidationResult(False, errors=errors)

        return ValidationResult(True, data=data)


class TemporalCheck(IntegrityCheck):
    """Integrity check for temporal consistency.

    This integrity check validates that temporal relationships between fields are valid.
    """

    def __init__(
        self,
        name: str,
        start_field: str,
        end_field: str,
        allow_equal: bool = True,
    ):
        """Initialize a temporal check.

        Args:
            name: The name of the integrity check
            start_field: The field containing the start time
            end_field: The field containing the end time
            allow_equal: Whether the start and end times can be equal
        """
        self._name = name
        self._start_field = start_field
        self._end_field = end_field
        self._allow_equal = allow_equal

    @property
    def name(self) -> str:
        """Get the name of the integrity check.

        Returns:
            The name of the integrity check
        """
        return self._name

    @property
    def check_type(self) -> IntegrityCheckType:
        """Get the type of integrity check.

        Returns:
            The type of integrity check
        """
        return IntegrityCheckType.TEMPORAL

    def check(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check data integrity.

        Args:
            data: The data to check
            context: Additional context for the check, or None if not needed

        Returns:
            The validation result
        """
        # Extract the values from the data
        if not isinstance(data, dict):
            return ValidationResult(
                False,
                errors={"temporal": f"Expected dictionary, got {type(data).__name__}"},
            )

        if self._start_field not in data:
            return ValidationResult(
                False,
                errors={
                    "temporal": f"Start field '{self._start_field}' not found in data"
                },
            )

        if self._end_field not in data:
            return ValidationResult(
                False,
                errors={"temporal": f"End field '{self._end_field}' not found in data"},
            )

        start_time = data[self._start_field]
        end_time = data[self._end_field]

        # If either value is None, we can't compare them
        if start_time is None or end_time is None:
            return ValidationResult(True, data=data)

        # Check if the start time is before the end time
        if self._allow_equal:
            if start_time > end_time:
                return ValidationResult(
                    False,
                    errors={
                        "temporal": f"Start time {start_time} is after end time {end_time}"
                    },
                )
        else:
            if start_time >= end_time:
                return ValidationResult(
                    False,
                    errors={
                        "temporal": f"Start time {start_time} is not before end time {end_time}"
                    },
                )

        return ValidationResult(True, data=data)


class IntegrityValidator(Validator):
    """Validator that uses integrity checks.

    This validator applies one or more integrity checks to data.
    """

    def __init__(self, name: str, checks: List[IntegrityCheck]):
        """Initialize an integrity validator.

        Args:
            name: The name of the validator
            checks: The integrity checks to apply
        """
        self._name = name
        self._checks = checks

    @property
    def name(self) -> str:
        """Get the name of the validator.

        Returns:
            The name of the validator
        """
        return self._name

    @property
    def checks(self) -> List[IntegrityCheck]:
        """Get the integrity checks.

        Returns:
            The integrity checks
        """
        return self._checks

    def validate(self, data: Any) -> ValidationResult:
        """Validate data.

        Args:
            data: The data to validate

        Returns:
            The validation result
        """
        all_errors = {}
        current_data = data

        for check in self._checks:
            result = check.check(current_data)
            if not result.is_valid:
                # Add errors from this check
                for key, value in result.errors.items():
                    all_errors[f"{check.name}.{key}"] = value
            else:
                # Update the data for the next check
                current_data = result.data

        if all_errors:
            return ValidationResult(False, errors=all_errors)
        else:
            return ValidationResult(True, data=current_data)


# Registry for integrity checks
_integrity_checks: Dict[str, IntegrityCheck] = {}


def register_integrity_check(check: IntegrityCheck) -> None:
    """Register an integrity check.

    Args:
        check: The integrity check to register

    Raises:
        ValidationError: If the integrity check is already registered
    """
    if check.name in _integrity_checks:
        raise ValidationError(
            message=f"Integrity check '{check.name}' is already registered"
        )
    _integrity_checks[check.name] = check


def get_integrity_check(name: str) -> IntegrityCheck:
    """Get an integrity check.

    Args:
        name: The name of the integrity check to get

    Returns:
        The integrity check

    Raises:
        ValidationError: If the integrity check is not registered
    """
    if name not in _integrity_checks:
        raise ValidationError(message=f"Integrity check '{name}' is not registered")
    return _integrity_checks[name]


def register_integrity_validator(
    name: str, checks: List[Union[IntegrityCheck, str]]
) -> None:
    """Register an integrity validator.

    Args:
        name: The name of the validator
        checks: The integrity checks to apply, either as IntegrityCheck objects or the names of registered integrity checks

    Raises:
        ValidationError: If the validator is already registered
        ValidationError: If a named integrity check is not registered
    """
    # Resolve integrity check names to objects
    resolved_checks = []
    for check in checks:
        if isinstance(check, str):
            resolved_checks.append(get_integrity_check(check))
        else:
            resolved_checks.append(check)

    # Create and register the integrity validator
    validator = IntegrityValidator(name, resolved_checks)
    register_validator(validator)


def create_integrity_validation_hook(
    validator: Union[Validator, str],
    stage: ValidationStage,
    level: ValidationLevel = ValidationLevel.STANDARD,
    condition: Optional[Callable[[Any, Dict[str, Any]], bool]] = None,
) -> ValidationHook:
    """Create a validation hook for integrity validation.

    Args:
        validator: The validator to use, either as a Validator object or the name of a registered validator
        stage: The stage at which to validate
        level: The level of validation to perform
        condition: A function that determines whether to apply the validator,
            or None to always apply it

    Returns:
        The validation hook

    Raises:
        ValidationError: If a named validator is not registered
    """
    from pepperpy.data.validation import create_validation_hook

    return create_validation_hook(validator, stage, level, condition)


# Convenience functions for creating common integrity checks


def create_referential_integrity_check(
    name: str,
    source_field: str,
    target_entity: str,
    target_field: str,
    resolver: Callable[[Any, str], bool],
) -> ReferentialIntegrityCheck:
    """Create a referential integrity check.

    Args:
        name: The name of the integrity check
        source_field: The field in the source entity that contains the reference
        target_entity: The name of the target entity
        target_field: The field in the target entity that is referenced
        resolver: A function that checks if a reference exists in the target entity

    Returns:
        The referential integrity check
    """
    check = ReferentialIntegrityCheck(
        name=name,
        source_field=source_field,
        target_entity=target_entity,
        target_field=target_field,
        resolver=resolver,
    )
    register_integrity_check(check)
    return check


def create_uniqueness_check(
    name: str,
    fields: Union[str, List[str]],
    resolver: Callable[[Any, Union[str, List[str]]], bool],
) -> UniquenessCheck:
    """Create a uniqueness check.

    Args:
        name: The name of the integrity check
        fields: The field or fields that must have unique values
        resolver: A function that checks if values are unique

    Returns:
        The uniqueness check
    """
    check = UniquenessCheck(
        name=name,
        fields=fields,
        resolver=resolver,
    )
    register_integrity_check(check)
    return check


def create_range_check(
    name: str,
    field: str,
    min_value: Optional[Any] = None,
    max_value: Optional[Any] = None,
    inclusive_min: bool = True,
    inclusive_max: bool = True,
) -> RangeCheck:
    """Create a range check.

    Args:
        name: The name of the integrity check
        field: The field to check
        min_value: The minimum allowed value, or None for no minimum
        max_value: The maximum allowed value, or None for no maximum
        inclusive_min: Whether the minimum value is inclusive
        inclusive_max: Whether the maximum value is inclusive

    Returns:
        The range check
    """
    check = RangeCheck(
        name=name,
        field=field,
        min_value=min_value,
        max_value=max_value,
        inclusive_min=inclusive_min,
        inclusive_max=inclusive_max,
    )
    register_integrity_check(check)
    return check


def create_format_check(
    name: str,
    field: str,
    format_validator: Callable[[Any], bool],
    error_message: str,
) -> FormatCheck:
    """Create a format check.

    Args:
        name: The name of the integrity check
        field: The field to check
        format_validator: A function that checks if a value matches the required format
        error_message: The error message to use if validation fails

    Returns:
        The format check
    """
    check = FormatCheck(
        name=name,
        field=field,
        format_validator=format_validator,
        error_message=error_message,
    )
    register_integrity_check(check)
    return check


def create_completeness_check(
    name: str,
    required_fields: List[str],
    allow_empty: bool = False,
) -> CompletenessCheck:
    """Create a completeness check.

    Args:
        name: The name of the integrity check
        required_fields: The fields that are required
        allow_empty: Whether empty values (empty strings, empty lists, etc.) are allowed

    Returns:
        The completeness check
    """
    check = CompletenessCheck(
        name=name,
        required_fields=required_fields,
        allow_empty=allow_empty,
    )
    register_integrity_check(check)
    return check


def create_temporal_check(
    name: str,
    start_field: str,
    end_field: str,
    allow_equal: bool = True,
) -> TemporalCheck:
    """Create a temporal check.

    Args:
        name: The name of the integrity check
        start_field: The field containing the start time
        end_field: The field containing the end time
        allow_equal: Whether the start and end times can be equal

    Returns:
        The temporal check
    """
    check = TemporalCheck(
        name=name,
        start_field=start_field,
        end_field=end_field,
        allow_equal=allow_equal,
    )
    register_integrity_check(check)
    return check
