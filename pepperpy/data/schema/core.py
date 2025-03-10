"""Core functionality for schema module.

This module provides the core functionality for schema validation and management.
"""

from abc import ABC, abstractmethod
from dataclasses import is_dataclass
from enum import Enum
from typing import Any, Dict, List, Type, TypeVar, get_type_hints

from pydantic import BaseModel, create_model
from pydantic import ValidationError as PydanticValidationError

from pepperpy.data.errors import SchemaError, ValidationError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for schema types
T = TypeVar("T")


class SchemaType(Enum):
    """Type of schema."""

    PYDANTIC = "pydantic"
    DATACLASS = "dataclass"
    JSON_SCHEMA = "json_schema"


class Schema(ABC):
    """Base class for schemas.

    Schemas are responsible for validating and transforming data.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the schema.

        Returns:
            The name of the schema
        """
        pass

    @property
    @abstractmethod
    def schema_type(self) -> SchemaType:
        """Get the type of the schema.

        Returns:
            The type of the schema
        """
        pass

    @abstractmethod
    def validate(self, data: Any) -> Any:
        """Validate data against the schema.

        Args:
            data: The data to validate

        Returns:
            The validated data

        Raises:
            ValidationError: If the data is invalid
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary.

        Returns:
            The schema as a dictionary
        """
        pass

    @abstractmethod
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert the schema to a JSON schema.

        Returns:
            The schema as a JSON schema
        """
        pass


class PydanticSchema(Schema):
    """Schema based on Pydantic models.

    This schema uses Pydantic models for validation.
    """

    def __init__(self, model: Type[BaseModel]):
        """Initialize a Pydantic schema.

        Args:
            model: The Pydantic model to use for validation
        """
        self._model = model

    @property
    def name(self) -> str:
        """Get the name of the schema.

        Returns:
            The name of the schema
        """
        return self._model.__name__

    @property
    def schema_type(self) -> SchemaType:
        """Get the type of the schema.

        Returns:
            The type of the schema
        """
        return SchemaType.PYDANTIC

    @property
    def model(self) -> Type[BaseModel]:
        """Get the Pydantic model.

        Returns:
            The Pydantic model
        """
        return self._model

    def validate(self, data: Any) -> Any:
        """Validate data against the schema.

        Args:
            data: The data to validate

        Returns:
            The validated data

        Raises:
            ValidationError: If the data is invalid
        """
        try:
            return self._model.model_validate(data)
        except PydanticValidationError as e:
            errors = []
            for error in e.errors():
                field_name = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{field_name}: {error['msg']}")

            raise ValidationError(
                f"Validation failed: {', '.join(errors)}",
                schema_name=self.name,
                details={"errors": e.errors()},
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary.

        Returns:
            The schema as a dictionary
        """
        return {
            "name": self.name,
            "type": self.schema_type.value,
            "schema": self._model.model_json_schema(),
        }

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert the schema to a JSON schema.

        Returns:
            The schema as a JSON schema
        """
        return self._model.model_json_schema()


class DataclassSchema(Schema):
    """Schema based on dataclasses.

    This schema uses dataclasses for validation.
    """

    def __init__(self, dataclass_type: Type[Any]):
        """Initialize a dataclass schema.

        Args:
            dataclass_type: The dataclass to use for validation

        Raises:
            SchemaError: If the type is not a dataclass
        """
        if not is_dataclass(dataclass_type):
            raise SchemaError(f"Type {dataclass_type.__name__} is not a dataclass")

        self._dataclass_type = dataclass_type

    @property
    def name(self) -> str:
        """Get the name of the schema.

        Returns:
            The name of the schema
        """
        return self._dataclass_type.__name__

    @property
    def schema_type(self) -> SchemaType:
        """Get the type of the schema.

        Returns:
            The type of the schema
        """
        return SchemaType.DATACLASS

    @property
    def dataclass_type(self) -> Type[Any]:
        """Get the dataclass type.

        Returns:
            The dataclass type
        """
        return self._dataclass_type

    def validate(self, data: Any) -> Any:
        """Validate data against the schema.

        Args:
            data: The data to validate

        Returns:
            The validated data

        Raises:
            ValidationError: If the data is invalid
        """
        try:
            # Convert to Pydantic model for validation
            model = self._to_pydantic_model()
            validated = model.model_validate(data)

            # Convert back to dataclass
            return self._dataclass_type(**validated.model_dump())
        except PydanticValidationError as e:
            errors = []
            for error in e.errors():
                field_name = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{field_name}: {error['msg']}")

            raise ValidationError(
                f"Validation failed: {', '.join(errors)}",
                schema_name=self.name,
                details={"errors": e.errors()},
            )
        except Exception as e:
            raise ValidationError(
                f"Validation failed: {e}",
                schema_name=self.name,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary.

        Returns:
            The schema as a dictionary
        """
        return {
            "name": self.name,
            "type": self.schema_type.value,
            "schema": self.to_json_schema(),
        }

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert the schema to a JSON schema.

        Returns:
            The schema as a JSON schema
        """
        model = self._to_pydantic_model()
        return model.model_json_schema()

    def _to_pydantic_model(self) -> Type[BaseModel]:
        """Convert the dataclass to a Pydantic model.

        Returns:
            The Pydantic model
        """
        type_hints = get_type_hints(self._dataclass_type)
        fields = {}

        for field_name, field_type in type_hints.items():
            default = None
            for field_obj in self._dataclass_type.__dataclass_fields__.values():
                if field_obj.name == field_name:
                    if field_obj.default is not field_obj.default_factory:
                        default = field_obj.default
                    break

            fields[field_name] = (field_type, default)

        return create_model(self.name, **fields)


class JsonSchema(Schema):
    """Schema based on JSON Schema.

    This schema uses JSON Schema for validation.
    """

    def __init__(self, name: str, schema: Dict[str, Any]):
        """Initialize a JSON schema.

        Args:
            name: The name of the schema
            schema: The JSON schema
        """
        self._name = name
        self._schema = schema

    @property
    def name(self) -> str:
        """Get the name of the schema.

        Returns:
            The name of the schema
        """
        return self._name

    @property
    def schema_type(self) -> SchemaType:
        """Get the type of the schema.

        Returns:
            The type of the schema
        """
        return SchemaType.JSON_SCHEMA

    def validate(self, data: Any) -> Any:
        """Validate data against the schema.

        Args:
            data: The data to validate

        Returns:
            The validated data

        Raises:
            ValidationError: If the data is invalid
        """
        try:
            # Convert to Pydantic model for validation
            model = self._to_pydantic_model()
            return model.model_validate(data)
        except PydanticValidationError as e:
            errors = []
            for error in e.errors():
                field_name = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{field_name}: {error['msg']}")

            raise ValidationError(
                f"Validation failed: {', '.join(errors)}",
                schema_name=self.name,
                details={"errors": e.errors()},
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary.

        Returns:
            The schema as a dictionary
        """
        return {
            "name": self.name,
            "type": self.schema_type.value,
            "schema": self._schema,
        }

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert the schema to a JSON schema.

        Returns:
            The schema as a JSON schema
        """
        return self._schema

    def _to_pydantic_model(self) -> Type[BaseModel]:
        """Convert the JSON schema to a Pydantic model.

        Returns:
            The Pydantic model
        """
        # Create a model from the JSON schema
        model_name = self.name
        schema = self._schema

        # Create a new model class
        class Model(BaseModel):
            model_config = {"title": model_name}

        # Set the JSON schema
        setattr(Model, "__json_schema__", schema)

        return Model


class SchemaRegistry:
    """Registry for schemas.

    The schema registry is responsible for managing schemas.
    """

    def __init__(self):
        """Initialize a schema registry."""
        self._schemas: Dict[str, Schema] = {}

    def register(self, schema: Schema) -> None:
        """Register a schema.

        Args:
            schema: The schema to register

        Raises:
            SchemaError: If a schema with the same name is already registered
        """
        if schema.name in self._schemas:
            raise SchemaError(f"Schema '{schema.name}' is already registered")

        self._schemas[schema.name] = schema

    def unregister(self, name: str) -> None:
        """Unregister a schema.

        Args:
            name: The name of the schema to unregister

        Raises:
            SchemaError: If the schema is not registered
        """
        if name not in self._schemas:
            raise SchemaError(f"Schema '{name}' is not registered")

        del self._schemas[name]

    def get(self, name: str) -> Schema:
        """Get a schema by name.

        Args:
            name: The name of the schema

        Returns:
            The schema

        Raises:
            SchemaError: If the schema is not registered
        """
        if name not in self._schemas:
            raise SchemaError(f"Schema '{name}' is not registered")

        return self._schemas[name]

    def list(self) -> List[str]:
        """List all registered schemas.

        Returns:
            The names of all registered schemas
        """
        return list(self._schemas.keys())

    def clear(self) -> None:
        """Clear all registered schemas."""
        self._schemas.clear()


# Default schema registry
_registry = SchemaRegistry()


def get_registry() -> SchemaRegistry:
    """Get the default schema registry.

    Returns:
        The default schema registry
    """
    return _registry


def set_registry(registry: SchemaRegistry) -> None:
    """Set the default schema registry.

    Args:
        registry: The schema registry to set as the default
    """
    global _registry
    _registry = registry


def register_schema(schema: Schema) -> None:
    """Register a schema in the default registry.

    Args:
        schema: The schema to register

    Raises:
        SchemaError: If a schema with the same name is already registered
    """
    get_registry().register(schema)


def unregister_schema(name: str) -> None:
    """Unregister a schema from the default registry.

    Args:
        name: The name of the schema to unregister

    Raises:
        SchemaError: If the schema is not registered
    """
    get_registry().unregister(name)


def get_schema(name: str) -> Schema:
    """Get a schema by name from the default registry.

    Args:
        name: The name of the schema

    Returns:
        The schema

    Raises:
        SchemaError: If the schema is not registered
    """
    return get_registry().get(name)


def list_schemas() -> List[str]:
    """List all registered schemas in the default registry.

    Returns:
        The names of all registered schemas
    """
    return get_registry().list()


def clear_schemas() -> None:
    """Clear all registered schemas in the default registry."""
    get_registry().clear()


def register_pydantic_model(model: Type[BaseModel]) -> None:
    """Register a Pydantic model as a schema.

    Args:
        model: The Pydantic model to register

    Raises:
        SchemaError: If a schema with the same name is already registered
    """
    schema = PydanticSchema(model)
    register_schema(schema)


def register_dataclass(dataclass_type: Type[Any]) -> None:
    """Register a dataclass as a schema.

    Args:
        dataclass_type: The dataclass to register

    Raises:
        SchemaError: If a schema with the same name is already registered
        SchemaError: If the type is not a dataclass
    """
    schema = DataclassSchema(dataclass_type)
    register_schema(schema)


def register_json_schema(name: str, schema: Dict[str, Any]) -> None:
    """Register a JSON schema.

    Args:
        name: The name of the schema
        schema: The JSON schema

    Raises:
        SchemaError: If a schema with the same name is already registered
    """
    schema_obj = JsonSchema(name, schema)
    register_schema(schema_obj)


def validate(data: Any, schema_name: str) -> Any:
    """Validate data against a schema.

    Args:
        data: The data to validate
        schema_name: The name of the schema

    Returns:
        The validated data

    Raises:
        SchemaError: If the schema is not registered
        ValidationError: If the data is invalid
    """
    schema = get_schema(schema_name)
    return schema.validate(data)
