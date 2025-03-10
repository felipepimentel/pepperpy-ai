"""Schema validation implementation.

This module provides functionality for validating data against schemas.
"""

from typing import Any, Dict, List, Optional, Type, Union, cast

from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo

from pepperpy.errors import ValidationError as PepperValidationError


class SchemaValidator:
    """Schema validator for data validation.

    This class provides functionality for validating data against schemas
    using Pydantic models.
    """

    def __init__(self) -> None:
        """Initialize the schema validator."""
        self._models: Dict[str, Type[BaseModel]] = {}

    def register_schema(
        self,
        name: str,
        schema: Dict[str, Any],
        description: Optional[str] = None,
    ) -> None:
        """Register a schema for validation.

        Args:
            name: Name of the schema.
            schema: Schema definition.
            description: Optional schema description.

        Raises:
            PepperValidationError: If schema registration fails.
        """
        try:
            # Create field definitions
            fields = {}
            for field_name, field_def in schema.items():
                # Get field type
                field_type = field_def.get("type", Any)
                if isinstance(field_type, str):
                    field_type = {
                        "string": str,
                        "integer": int,
                        "number": float,
                        "boolean": bool,
                        "array": List[Any],
                        "object": Dict[str, Any],
                    }.get(field_type, Any)

                # Get field constraints
                constraints = {}
                if "required" in field_def:
                    constraints["required"] = field_def["required"]
                if "default" in field_def:
                    constraints["default"] = field_def["default"]
                if "description" in field_def:
                    constraints["description"] = field_def["description"]

                # Add field to definitions
                fields[field_name] = (field_type, FieldInfo(**constraints))

            # Create model dynamically
            model_dict = {
                "__annotations__": {
                    field_name: field_type
                    for field_name, (field_type, _) in fields.items()
                },
                "__doc__": description,
                "__module__": __name__,
            }

            # Add field info
            for field_name, (_, field_info) in fields.items():
                model_dict[field_name] = field_info

            # Create model class
            model = type(name, (BaseModel,), model_dict)

            # Store model
            self._models[name] = model

        except Exception as e:
            raise PepperValidationError(f"Error registering schema: {str(e)}") from e

    def validate(
        self,
        name: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Validate data against a registered schema.

        Args:
            name: Name of the schema to validate against.
            data: Data to validate.

        Returns:
            Validated and possibly coerced data.

        Raises:
            PepperValidationError: If validation fails.
        """
        try:
            # Get model
            model = self._models.get(name)
            if not model:
                raise PepperValidationError(f"Schema {name} not found")

            # Validate single item or list
            if isinstance(data, list):
                return [
                    cast(Dict[str, Any], model(**item).model_dump()) for item in data
                ]
            else:
                return cast(Dict[str, Any], model(**data).model_dump())

        except ValidationError as e:
            raise PepperValidationError(str(e)) from e
        except Exception as e:
            raise PepperValidationError(f"Error validating data: {str(e)}") from e

    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a registered schema.

        Args:
            name: Name of the schema.

        Returns:
            Schema definition if found, None otherwise.
        """
        model = self._models.get(name)
        if not model:
            return None

        # Get model name and description
        model_name = getattr(model, "__name__", name)
        model_doc = getattr(model, "__doc__", "") or ""

        return {
            "title": model_name,
            "description": model_doc,
            "type": "object",
            "properties": {
                name: {
                    "type": field.annotation.__name__.lower(),
                    "description": field.description or "",
                    "required": field.is_required(),
                    "default": field.default if not field.is_required() else None,
                }
                for name, field in model.model_fields.items()
            },
        }

    def list_schemas(self) -> List[str]:
        """List registered schemas.

        Returns:
            List of schema names.
        """
        return list(self._models.keys())

    def clear(self) -> None:
        """Clear all registered schemas."""
        self._models.clear()
