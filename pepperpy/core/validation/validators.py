"""Core validation functionality for the Pepperpy framework."""

from typing import Any, Callable, Dict, List, Optional, Type, Union

from .base import Validator


class ContentValidator(Validator):
    """Validator for content data."""

    def __init__(self, content_type: str, rules: Dict[str, Any]):
        self.content_type = content_type
        self.rules = rules

    def validate(self, data: Any) -> bool:
        """Validate content data."""
        if not isinstance(data, (str, bytes)):
            return False

        # Check content type if specified
        if self.content_type:
            import mimetypes

            guessed_type = mimetypes.guess_type(str(data))[0]
            if guessed_type != self.content_type:
                return False

        # Apply validation rules
        for rule_name, rule_value in self.rules.items():
            validator = CONTENT_VALIDATORS.get(rule_name)
            if validator and not validator(data, rule_value):
                return False

        return True


class DataValidator(Validator):
    """Validator for structured data."""

    def __init__(self, data_type: Type, constraints: Optional[Dict[str, Any]] = None):
        self.data_type = data_type
        self.constraints = constraints or {}

    def validate(self, data: Any) -> bool:
        """Validate structured data."""
        # Type check
        if not isinstance(data, self.data_type):
            return False

        # Apply constraints
        for constraint_name, constraint_value in self.constraints.items():
            validator = DATA_VALIDATORS.get(constraint_name)
            if validator and not validator(data, constraint_value):
                return False

        return True


# Content validation functions
def validate_length(data: Union[str, bytes], max_length: int) -> bool:
    """Validate content length."""
    return len(data) <= max_length


def validate_pattern(data: str, pattern: str) -> bool:
    """Validate content against regex pattern."""
    import re

    return bool(re.match(pattern, str(data)))


# Data validation functions
def validate_range(
    data: float, range_spec: Dict[str, Union[int, float]],
) -> bool:
    """Validate numeric range."""
    min_val = range_spec.get("min")
    max_val = range_spec.get("max")

    if min_val is not None and data < min_val:
        return False
    if max_val is not None and data > max_val:
        return False
    return True


def validate_enum(data: Any, allowed_values: List[Any]) -> bool:
    """Validate enum values."""
    return data in allowed_values


# Register validators
CONTENT_VALIDATORS: Dict[str, Callable] = {
    "max_length": validate_length,
    "pattern": validate_pattern,
}

DATA_VALIDATORS: Dict[str, Callable] = {
    "range": validate_range,
    "enum": validate_enum,
}


class ValidatorRegistry:
    """Registry for validators."""

    _validators: Dict[str, Validator] = {}

    @classmethod
    def register(cls, name: str, validator: Validator) -> None:
        """Register a validator."""
        cls._validators[name] = validator

    @classmethod
    def get(cls, name: str) -> Optional[Validator]:
        """Get a registered validator."""
        return cls._validators.get(name)

    @classmethod
    def validate(cls, name: str, data: Any) -> bool:
        """Validate using a registered validator."""
        validator = cls.get(name)
        if not validator:
            raise ValueError(f"Validator not found: {name}")
        return validator.validate(data)
