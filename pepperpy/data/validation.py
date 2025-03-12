"""Validation functionality for data module.

This module provides functionality for data validation, including validators,
validation hooks, and validation pipelines. It integrates with the transformation
pipeline to provide validation at various stages of data processing.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from pepperpy.data.errors import ValidationError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables for data types
T = TypeVar("T")
U = TypeVar("U")


class ValidationLevel(Enum):
    """Validation level.

    This enum defines the level of validation to perform.
    """

    # Perform basic validation (e.g., type checking)
    BASIC = "basic"
    # Perform standard validation (e.g., format checking)
    STANDARD = "standard"
    # Perform strict validation (e.g., business rule checking)
    STRICT = "strict"


class ValidationStage(Enum):
    """Validation stage.

    This enum defines the stage at which validation is performed.
    """

    # Validate before transformation
    PRE_TRANSFORM = "pre_transform"
    # Validate after transformation
    POST_TRANSFORM = "post_transform"
    # Validate during transformation (between stages)
    INTERMEDIATE = "intermediate"


class ValidationResult:
    """Result of validation.

    This class represents the result of validation, including whether the data
    is valid and any validation errors.
    """

    def __init__(
        self, is_valid: bool, errors: Optional[Dict[str, str]] = None, data: Any = None
    ):
        """Initialize a validation result.

        Args:
            is_valid: Whether the data is valid
            errors: Validation errors, or None if the data is valid
            data: The validated data, or None if the data is invalid
        """
        self.is_valid = is_valid
        self.errors = errors or {}
        self.data = data

    def __bool__(self) -> bool:
        """Convert to boolean.

        Returns:
            True if the data is valid, False otherwise
        """
        return self.is_valid

    def raise_if_invalid(self) -> Any:
        """Raise an exception if the data is invalid.

        Returns:
            The validated data if valid

        Raises:
            ValidationError: If the data is invalid
        """
        if not self.is_valid:
            error_message = f"Validation failed: {', '.join(f'{k}: {v}' for k, v in self.errors.items())}"
            raise ValidationError(
                message=error_message, details={"errors": self.errors}
            )
        return self.data


class Validator(ABC):
    """Base class for validators.

    Validators are responsible for validating data.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the validator.

        Returns:
            The name of the validator
        """
        pass

    @abstractmethod
    def validate(self, data: Any) -> ValidationResult:
        """Validate data.

        Args:
            data: The data to validate

        Returns:
            The validation result
        """
        pass


class FunctionValidator(Validator):
    """Validator that uses a function.

    This validator uses a function to validate data.
    """

    def __init__(self, name: str, func: Callable[[Any], ValidationResult]):
        """Initialize a function validator.

        Args:
            name: The name of the validator
            func: The validation function
        """
        self._name = name
        self._func = func

    @property
    def name(self) -> str:
        """Get the name of the validator.

        Returns:
            The name of the validator
        """
        return self._name

    def validate(self, data: Any) -> ValidationResult:
        """Validate data.

        Args:
            data: The data to validate

        Returns:
            The validation result
        """
        return self._func(data)


class SchemaValidator(Validator):
    """Validator that uses a schema.

    This validator uses a schema to validate data.
    """

    def __init__(self, name: str, schema_name: str):
        """Initialize a schema validator.

        Args:
            name: The name of the validator
            schema_name: The name of the schema to validate against
        """
        self._name = name
        self._schema_name = schema_name

    @property
    def name(self) -> str:
        """Get the name of the validator.

        Returns:
            The name of the validator
        """
        return self._name

    @property
    def schema_name(self) -> str:
        """Get the name of the schema.

        Returns:
            The name of the schema
        """
        return self._schema_name

    def validate(self, data: Any) -> ValidationResult:
        """Validate data.

        Args:
            data: The data to validate

        Returns:
            The validation result
        """
        from pepperpy.data.schema import validate

        try:
            validated = validate(data, self._schema_name)
            return ValidationResult(True, data=validated)
        except ValidationError as e:
            # Extract error information from the exception
            error_dict = {}
            # Convert the exception to a string representation
            error_str = str(e)
            error_dict = {"validation": error_str}
            return ValidationResult(False, errors=error_dict)


class CompositeValidator(Validator):
    """Validator that combines multiple validators.

    This validator applies multiple validators to data.
    """

    def __init__(self, name: str, validators: List[Validator]):
        """Initialize a composite validator.

        Args:
            name: The name of the validator
            validators: The validators to apply
        """
        self._name = name
        self._validators = validators

    @property
    def name(self) -> str:
        """Get the name of the validator.

        Returns:
            The name of the validator
        """
        return self._name

    @property
    def validators(self) -> List[Validator]:
        """Get the validators.

        Returns:
            The validators
        """
        return self._validators

    def validate(self, data: Any) -> ValidationResult:
        """Validate data.

        Args:
            data: The data to validate

        Returns:
            The validation result
        """
        all_errors = {}
        current_data = data

        for validator in self._validators:
            result = validator.validate(current_data)
            if not result.is_valid:
                # Add errors from this validator
                for key, value in result.errors.items():
                    all_errors[f"{validator.name}.{key}"] = value
            else:
                # Update the data for the next validator
                current_data = result.data

        if all_errors:
            return ValidationResult(False, errors=all_errors)
        else:
            return ValidationResult(True, data=current_data)


class ValidationHook:
    """Validation hook.

    This class represents a validation hook that can be attached to a
    transformation pipeline to validate data at various stages.
    """

    def __init__(
        self,
        validator: Validator,
        stage: ValidationStage,
        level: ValidationLevel = ValidationLevel.STANDARD,
        condition: Optional[Callable[[Any, Dict[str, Any]], bool]] = None,
    ):
        """Initialize a validation hook.

        Args:
            validator: The validator to use
            stage: The stage at which to validate
            level: The level of validation to perform
            condition: A function that determines whether to apply the validator,
                or None to always apply it
        """
        self.validator = validator
        self.stage = stage
        self.level = level
        self.condition = condition

    def should_validate(self, data: Any, context: Dict[str, Any]) -> bool:
        """Check whether to validate.

        Args:
            data: The data to validate
            context: The pipeline context

        Returns:
            True if validation should be performed, False otherwise
        """
        # Check if validation is enabled for this level
        enabled_levels = context.get("validation_levels", [ValidationLevel.STANDARD])
        if self.level not in enabled_levels:
            return False

        # Check if the condition is met
        if self.condition is not None:
            return self.condition(data, context)

        return True

    def validate(self, data: Any, context: Dict[str, Any]) -> ValidationResult:
        """Validate data.

        Args:
            data: The data to validate
            context: The pipeline context

        Returns:
            The validation result
        """
        if not self.should_validate(data, context):
            return ValidationResult(True, data=data)

        return self.validator.validate(data)


# Registry for validators
_validators: Dict[str, Validator] = {}


def register_validator(validator: Validator) -> None:
    """Register a validator.

    Args:
        validator: The validator to register

    Raises:
        ValidationError: If the validator is already registered
    """
    if validator.name in _validators:
        raise ValidationError(
            message=f"Validator '{validator.name}' is already registered"
        )
    _validators[validator.name] = validator


def get_validator(name: str) -> Validator:
    """Get a validator.

    Args:
        name: The name of the validator to get

    Returns:
        The validator

    Raises:
        ValidationError: If the validator is not registered
    """
    if name not in _validators:
        raise ValidationError(message=f"Validator '{name}' is not registered")
    return _validators[name]


def register_function_validator(
    name: str, func: Callable[[Any], ValidationResult]
) -> None:
    """Register a function validator.

    Args:
        name: The name of the validator
        func: The validation function

    Raises:
        ValidationError: If the validator is already registered
    """
    validator = FunctionValidator(name, func)
    register_validator(validator)


def register_schema_validator(name: str, schema_name: str) -> None:
    """Register a schema validator.

    Args:
        name: The name of the validator
        schema_name: The name of the schema to validate against

    Raises:
        ValidationError: If the validator is already registered
    """
    validator = SchemaValidator(name, schema_name)
    register_validator(validator)


def register_composite_validator(
    name: str, validators: List[Union[Validator, str]]
) -> None:
    """Register a composite validator.

    Args:
        name: The name of the validator
        validators: The validators to apply, either as Validator objects or the names of registered validators

    Raises:
        ValidationError: If the validator is already registered
        ValidationError: If a named validator is not registered
    """
    # Resolve validator names to objects
    resolved_validators = []
    for v in validators:
        if isinstance(v, str):
            resolved_validators.append(get_validator(v))
        else:
            resolved_validators.append(v)

    # Create and register the composite validator
    validator = CompositeValidator(name, resolved_validators)
    register_validator(validator)


def validate_with(name: str, data: Any) -> ValidationResult:
    """Validate data using a registered validator.

    Args:
        name: The name of the validator to use
        data: The data to validate

    Returns:
        The validation result

    Raises:
        ValidationError: If the validator is not registered
    """
    validator = get_validator(name)
    return validator.validate(data)


def create_validation_hook(
    validator: Union[Validator, str],
    stage: ValidationStage,
    level: ValidationLevel = ValidationLevel.STANDARD,
    condition: Optional[Callable[[Any, Dict[str, Any]], bool]] = None,
) -> ValidationHook:
    """Create a validation hook.

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
    # Resolve validator name to object
    validator_obj = validator
    if isinstance(validator_obj, str):
        validator_obj = get_validator(validator_obj)

    return ValidationHook(
        validator=cast(Validator, validator_obj),
        stage=stage,
        level=level,
        condition=condition,
    )
