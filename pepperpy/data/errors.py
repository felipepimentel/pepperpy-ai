"""Error classes for data module.

This module contains error classes for the data module.
"""

from typing import Any, Dict, Optional

from pepperpy.errors import PepperPyError


class DataError(PepperPyError):
    """Base class for all data-related errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a data error.

        Args:
            message: The error message
            details: Additional details about the error
        """
        super().__init__(message, details=details)


class SchemaError(DataError):
    """Error related to schema operations."""

    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a schema error.

        Args:
            message: The error message
            schema_name: The name of the schema
            details: Additional details about the error
        """
        if schema_name:
            message = f"Schema '{schema_name}': {message}"
        super().__init__(message, details=details)


class ValidationError(SchemaError):
    """Error related to schema validation."""

    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        field_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a validation error.

        Args:
            message: The error message
            schema_name: The name of the schema
            field_name: The name of the field
            details: Additional details about the error
        """
        if field_name:
            message = f"Field '{field_name}': {message}"
        super().__init__(message, schema_name=schema_name, details=details)


class TransformError(DataError):
    """Error related to data transformation."""

    def __init__(
        self,
        message: str,
        transform_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a transform error.

        Args:
            message: The error message
            transform_name: The name of the transform
            details: Additional details about the error
        """
        if transform_name:
            message = f"Transform '{transform_name}': {message}"
        super().__init__(message, details=details)


class PersistenceError(DataError):
    """Error related to data persistence."""

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a persistence error.

        Args:
            message: The error message
            provider_name: The name of the provider
            details: Additional details about the error
        """
        if provider_name:
            message = f"Provider '{provider_name}': {message}"
        super().__init__(message, details=details)


class ConnectionError(PersistenceError):
    """Error related to database connection."""

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a connection error.

        Args:
            message: The error message
            provider_name: The name of the provider
            details: Additional details about the error
        """
        super().__init__(
            f"Connection error: {message}", provider_name=provider_name, details=details
        )


class QueryError(PersistenceError):
    """Error related to database queries."""

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        provider_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a query error.

        Args:
            message: The error message
            query: The query that caused the error
            provider_name: The name of the provider
            details: Additional details about the error
        """
        if query:
            details = details or {}
            details["query"] = query
        super().__init__(
            f"Query error: {message}", provider_name=provider_name, details=details
        )
