"""Data module.

This module provides functionality for data handling, including schema validation,
data transformation, and persistence.
"""

from pepperpy.data.errors import (
    ConnectionError,
    DataError,
    PersistenceError,
    QueryError,
    SchemaError,
    TransformError,
    ValidationError,
)

__all__ = [
    "ConnectionError",
    "DataError",
    "PersistenceError",
    "QueryError",
    "SchemaError",
    "TransformError",
    "ValidationError",
]
