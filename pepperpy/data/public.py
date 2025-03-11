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
]
