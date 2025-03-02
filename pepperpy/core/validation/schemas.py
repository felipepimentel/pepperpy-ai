"""Schema definitions and format validation for the Pepperpy framework."""

from typing import Any, Callable, Dict, List, Optional


class SchemaDefinition:
    """Base class for schema definitions."""

    def __init__(self, schema_type: str, properties: Dict[str, Any]):
        self.schema_type = schema_type
        self.properties = properties
        self.required: List[str] = properties.get("required", [])
        self.format: Optional[str] = properties.get("format")

    def validate(self, data: Any) -> bool:
        """Validate data against the schema."""
        if not isinstance(data, dict):
            return False

        # Validate required fields
        for field in self.required:
            if field not in data:
                return False

        # Validate format if specified
        if self.format and not FormatValidator.validate(data, self.format):
            return False

        return True


class FormatValidator:
    """Validator for different data formats."""

    @staticmethod
    def validate(data: Any, format_type: str) -> bool:
        """Validate data against a specific format."""
        validator = FORMAT_VALIDATORS.get(format_type)
        if not validator:
            raise ValueError(f"Unknown format type: {format_type}")
        return validator(data)

    @staticmethod
    def register_format(format_type: str, validator_func: Callable) -> None:
        """Register a new format validator."""
        FORMAT_VALIDATORS[format_type] = validator_func


# Format validator functions
def validate_date_time(data: str) -> bool:
    """Validate ISO 8601 date-time format."""
    from datetime import datetime

    try:
        datetime.fromisoformat(data.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


def validate_email(data: str) -> bool:
    """Validate email format."""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, str(data)))


def validate_uri(data: str) -> bool:
    """Validate URI format."""
    from urllib.parse import urlparse

    try:
        result = urlparse(str(data))
        return all([result.scheme, result.netloc])
    except Exception:
        return False


# Register default format validators
FORMAT_VALIDATORS: Dict[str, Callable] = {
    "date-time": validate_date_time,
    "email": validate_email,
    "uri": validate_uri,
}


class SchemaRegistry:
    """Registry for schema definitions."""

    _schemas: Dict[str, SchemaDefinition] = {}

    @classmethod
    def register(cls, name: str, schema: SchemaDefinition) -> None:
        """Register a schema definition."""
        cls._schemas[name] = schema

    @classmethod
    def get(cls, name: str) -> Optional[SchemaDefinition]:
        """Get a registered schema by name."""
        return cls._schemas.get(name)

    @classmethod
    def validate(cls, name: str, data: Any) -> bool:
        """Validate data against a registered schema."""
        schema = cls.get(name)
        if not schema:
            raise ValueError(f"Schema not found: {name}")
        return schema.validate(data)
