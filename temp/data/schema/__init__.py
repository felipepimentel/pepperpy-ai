"""Schema module.

This module provides functionality for schema validation and management.
"""

from pepperpy.data.schema.core import (
    DataclassSchema,
    JsonSchema,
    PydanticSchema,
    Schema,
    SchemaRegistry,
    SchemaType,
    clear_schemas,
    get_registry,
    get_schema,
    list_schemas,
    register_dataclass,
    register_json_schema,
    register_pydantic_model,
    register_schema,
    set_registry,
    unregister_schema,
    validate,
)

__all__ = [
    "DataclassSchema",
    "JsonSchema",
    "PydanticSchema",
    "Schema",
    "SchemaRegistry",
    "SchemaType",
    "clear_schemas",
    "get_registry",
    "get_schema",
    "list_schemas",
    "register_dataclass",
    "register_json_schema",
    "register_pydantic_model",
    "register_schema",
    "set_registry",
    "unregister_schema",
    "validate",
]
