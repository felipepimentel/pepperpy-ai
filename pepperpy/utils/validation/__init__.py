"""Data validation utilities.

This module provides utility functions for validating data against schemas.
"""

import logging
from typing import Any

import jsonschema

from pepperpy.core.errors import ValidationError as PepperValidationError
from pepperpy.core.models import BaseModel
from pepperpy.processing.validators import DataValidator, DataValidatorConfig

logger = logging.getLogger(__name__)


class SchemaFormat:
    """Schema format constants."""

    JSON_SCHEMA = "json_schema"
    PYDANTIC = "pydantic"
    DICT = "dict"


async def validate_data(
    data: Any,
    schema: dict[str, Any] | type[BaseModel] | None,
    schema_format: str = SchemaFormat.JSON_SCHEMA,
) -> None:
    """Validate data against schema.

    Args:
        data: Data to validate
        schema: Validation schema
        schema_format: Schema format (json_schema, pydantic, dict)

    Raises:
        ValidationError: If validation fails
    """
    try:
        if schema is None:
            return

        if schema_format == SchemaFormat.JSON_SCHEMA:
            if not isinstance(schema, dict):
                raise PepperValidationError("JSON Schema must be a dictionary")
            validator = DataValidator(DataValidatorConfig(schema=schema))
            await validator.validate(data)
        elif schema_format == SchemaFormat.PYDANTIC:
            if not isinstance(schema, type) or not issubclass(schema, BaseModel):
                raise PepperValidationError("Pydantic schema must be a model class")
            _validate_pydantic(data, schema)
        elif schema_format == SchemaFormat.DICT:
            if not isinstance(schema, dict):
                raise PepperValidationError("Dictionary schema must be a dictionary")
            validator = DataValidator(DataValidatorConfig(field_types=schema))
            await validator.validate(data)
        else:
            raise PepperValidationError(f"Unsupported schema format: {schema_format}")

    except Exception as e:
        logger.error(
            f"Data validation failed: {e}",
            extra={"schema_format": schema_format},
            exc_info=True,
        )
        raise PepperValidationError(f"Failed to validate data: {e}") from e


def _validate_json_schema(data: Any, schema: dict[str, Any]) -> None:
    """Validate data against JSON Schema.

    Args:
        data: Data to validate
        schema: JSON Schema

    Raises:
        ValidationError: If validation fails
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        raise PepperValidationError(f"JSON Schema validation failed: {e}")


def _validate_pydantic(data: Any, model: type[BaseModel]) -> None:
    """Validate data against Pydantic model.

    Args:
        data: Data to validate
        model: Pydantic model class

    Raises:
        ValidationError: If validation fails
    """
    try:
        if isinstance(data, dict):
            model(**data)
        elif isinstance(data, model):
            return
        else:
            raise PepperValidationError("Data must be dict or Pydantic model")
    except Exception as e:
        raise PepperValidationError(f"Pydantic validation failed: {e}")


def _validate_dict(data: Any, schema: dict[str, Any]) -> None:
    """Validate dictionary data.

    Args:
        data: Data to validate
        schema: Dictionary schema

    Raises:
        ValidationError: If validation fails
    """
    try:
        if not isinstance(data, dict):
            raise PepperValidationError("Data must be a dictionary")

        for key, value_type in schema.items():
            if key not in data:
                raise PepperValidationError(f"Missing required key: {key}")
            if not isinstance(data[key], value_type):
                raise PepperValidationError(
                    f"Invalid type for key '{key}': "
                    f"expected {value_type.__name__}, "
                    f"got {type(data[key]).__name__}"
                )
    except Exception as e:
        raise PepperValidationError(f"Dictionary validation failed: {e}")
