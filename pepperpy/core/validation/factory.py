"""Factory for creating validators."""

from typing import Any, Dict

from .schemas import SchemaDefinition
from .validators import ContentValidator, DataValidator, Validator


class SchemaValidator(Validator):
    """Validator that uses a schema definition."""

    def __init__(self, schema: SchemaDefinition):
        self.schema = schema

    def validate(self, data: Any) -> bool:
        """Validate data using the schema."""
        return self.schema.validate(data)


class ValidatorFactory:
    """Factory for creating validators."""

    @classmethod
    def create_validator(cls, config: Dict[str, Any]) -> Validator:
        """Create a validator based on configuration."""
        validator_type = config.get("type", "data")

        if validator_type == "content":
            return cls._create_content_validator(config)
        elif validator_type == "data":
            return cls._create_data_validator(config)
        elif validator_type == "schema":
            return cls._create_schema_validator(config)
        else:
            raise ValueError(f"Unknown validator type: {validator_type}")

    @classmethod
    def _create_content_validator(cls, config: Dict[str, Any]) -> ContentValidator:
        """Create a content validator."""
        content_type = config.get("content_type", "")
        rules = config.get("rules", {})
        return ContentValidator(content_type, rules)

    @classmethod
    def _create_data_validator(cls, config: Dict[str, Any]) -> DataValidator:
        """Create a data validator."""
        data_type = config.get("data_type", object)
        constraints = config.get("constraints", {})
        return DataValidator(data_type, constraints)

    @classmethod
    def _create_schema_validator(cls, config: Dict[str, Any]) -> SchemaValidator:
        """Create a schema validator."""
        schema_type = config.get("schema_type", "object")
        properties = config.get("properties", {})
        schema = SchemaDefinition(schema_type, properties)
        return SchemaValidator(schema)
