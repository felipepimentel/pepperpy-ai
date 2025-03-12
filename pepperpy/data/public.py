"""Public API for data handling.

This module provides functions and classes for schema validation,
data transformation, and persistence.
"""

# Keep legacy imports for backward compatibility
from pepperpy.data.core import check, clear_data, list_keys

# Import errors
from pepperpy.data.errors import (
    ConnectionError,
    DataError,
    PersistenceError,
    SchemaError,
    ValidationError,
)

# Import from new providers directory
from pepperpy.data.providers import (
    BaseProvider,
    NoSQLProvider,
    ObjectStoreProvider,
    SQLProvider,
)

# Import schema validation
from pepperpy.data.schema import (
    Schema,
    SchemaRegistry,
    get_schema,
    list_schemas,
    validate,
)
from pepperpy.data.schema import (
    register_schema as add_schema,
)
from pepperpy.data.schema import (
    unregister_schema as remove_schema,
)

# Import transformation functions
from pepperpy.data.transform import (
    flatten,
    jsonify,
    map_data,
    merge,
    normalize,
    parse_date,
    parse_datetime,
    transform,
)

# Import transform pipeline with validation hooks
from pepperpy.data.transform_pipeline import (
    ValidatedPipeline,
    create_validated_pipeline,
    execute_validated_pipeline,
    get_validated_pipeline,
    register_validated_pipeline,
)

# Import validation functions
from pepperpy.data.validation import (
    ValidationLevel,
    ValidationResult,
    ValidationStage,
    Validator,
    get_validator,
    register_validator,
    validate_with,
)

__all__ = [
    # Errors
    "ConnectionError",
    "DataError",
    "PersistenceError",
    "SchemaError",
    "ValidationError",
    # Providers
    "BaseProvider",
    "NoSQLProvider",
    "ObjectStoreProvider",
    "SQLProvider",
    # Schema validation
    "Schema",
    "SchemaRegistry",
    "add_schema",
    "get_schema",
    "list_schemas",
    "remove_schema",
    "validate",
    # Persistence
    "check",
    "clear_data",
    "list_keys",
    # Data transformation
    "flatten",
    "jsonify",
    "map_data",
    "merge",
    "normalize",
    "parse_date",
    "parse_datetime",
    "transform",
    # Data validation
    "ValidationLevel",
    "ValidationResult",
    "ValidationStage",
    "Validator",
    "get_validator",
    "register_validator",
    "validate_with",
    # Transform pipeline with validation hooks
    "ValidatedPipeline",
    "create_validated_pipeline",
    "execute_validated_pipeline",
    "get_validated_pipeline",
    "register_validated_pipeline",
]
