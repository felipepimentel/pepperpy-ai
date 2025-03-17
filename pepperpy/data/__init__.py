"""Data module.

This module provides functionality for data handling, including schema validation,
data transformation, and persistence.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List, Optional, TypeVar

# Core errors
from pepperpy.core.errors import (
    NetworkError,
    PepperPyError,
    QueryError,
    SchemaError,
    StorageError,
    TransformError,
    ValidationError,
)

# Storage provider classes
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for data types
T = TypeVar("T")
U = TypeVar("U")


# Storage types and provider classes
class StorageType(Enum):
    """Type of storage."""

    MEMORY = "memory"
    FILE = "file"
    DATABASE = "database"
    CLOUD = "cloud"


class StorageProvider(ABC):
    """Base class for storage providers.

    Storage providers are responsible for storing and retrieving data.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the provider.

        Returns:
            The name of the provider
        """
        pass

    @property
    @abstractmethod
    def storage_type(self) -> StorageType:
        """Get the type of storage.

        Returns:
            The type of storage
        """
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the storage.

        Raises:
            ConnectionError: If there is an error connecting to the storage
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the storage.

        Raises:
            ConnectionError: If there is an error disconnecting from the storage
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if the provider is connected.

        Returns:
            True if the provider is connected, False otherwise
        """
        pass

    @abstractmethod
    async def store(self, key: str, data: Any) -> None:
        """Store data in the storage.

        Args:
            key: The key to store under
            data: The data to store

        Raises:
            StorageError: If there is an error storing the data
        """
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Any:
        """Retrieve data from the storage.

        Args:
            key: The key to retrieve

        Returns:
            The data

        Raises:
            StorageError: If there is an error retrieving the data
        """
        pass

    @abstractmethod
    async def remove(self, key: str) -> None:
        """Remove data from the storage.

        Args:
            key: The key to remove

        Raises:
            StorageError: If there is an error removing the data
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if data exists in the storage.

        Args:
            key: The key to check

        Returns:
            True if the data exists, False otherwise

        Raises:
            StorageError: If there is an error checking the data
        """
        pass

    @abstractmethod
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """List keys in the storage.

        Args:
            pattern: The pattern to match keys against

        Returns:
            A list of keys

        Raises:
            StorageError: If there is an error listing keys
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all data in the storage.

        Raises:
            StorageError: If there is an error clearing the data
        """
        pass


# Registry of storage providers
_providers: dict[str, StorageProvider] = {}


def register_provider(provider: StorageProvider) -> None:
    """Register a storage provider.

    Args:
        provider: The provider to register
    """
    _providers[provider.name] = provider
    logger.info(f"Registered storage provider: {provider.name}")


def unregister_provider(name: str) -> None:
    """Unregister a storage provider.

    Args:
        name: The name of the provider to unregister
    """
    if name in _providers:
        del _providers[name]
        logger.info(f"Unregistered storage provider: {name}")


def get_provider(name: str) -> StorageProvider:
    """Get a storage provider.

    Args:
        name: The name of the provider to get

    Returns:
        The provider

    Raises:
        StorageError: If the provider is not registered
    """
    if name not in _providers:
        raise StorageError(f"Storage provider not found: {name}")
    return _providers[name]


def list_providers() -> List[str]:
    """List registered storage providers.

    Returns:
        A list of provider names
    """
    return list(_providers.keys())


# Import from providers directory
from pepperpy.data.providers import (
    CloudProvider,
    DataProvider,
    FileProvider,
    NoSQLProvider,
    RESTProvider,
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
from pepperpy.providers.base import Provider


async def validate_and_transform(
    data: Any, schema_name: str, transform_name: Optional[str] = None
) -> Any:
    """Validate and transform data.

    Args:
        data: The data to validate and transform
        schema_name: The name of the schema to validate against
        transform_name: The name of the transform to apply

    Returns:
        The validated and transformed data

    Raises:
        SchemaError: If the schema is not registered
        ValidationError: If the data is invalid
        TransformError: If the transform is not registered
        TransformError: If there is an error transforming the data
    """
    # Validate the data
    validated = validate(data, schema_name)

    # Transform the data if a transform is specified
    if transform_name is not None:
        return transform(validated, transform_name)

    return validated


async def store(
    data: Any,
    provider_name: str,
    key: str,
    schema_name: Optional[str] = None,
    transform_name: Optional[str] = None,
) -> None:
    """Store data.

    Args:
        data: The data to store
        provider_name: The name of the provider to use
        key: The key to store the data under
        schema_name: The name of the schema to validate against
        transform_name: The name of the transform to apply

    Raises:
        SchemaError: If the schema is not registered
        ValidationError: If the data is invalid
        TransformError: If the transform is not registered
        TransformError: If there is an error transforming the data
        ProviderError: If the provider is not registered
        StorageError: If there is an error storing the data
    """
    # Validate and transform the data if a schema is specified
    if schema_name is not None:
        data = await validate_and_transform(data, schema_name, transform_name)

    # Get the provider
    provider = get_provider(provider_name)

    # Store the data
    await provider.store(key, data)


async def retrieve(
    provider_name: str,
    key: str,
    schema_name: Optional[str] = None,
    transform_name: Optional[str] = None,
) -> Any:
    """Retrieve data.

    Args:
        provider_name: The name of the provider to use
        key: The key to retrieve the data from
        schema_name: The name of the schema to validate against
        transform_name: The name of the transform to apply

    Returns:
        The retrieved data

    Raises:
        ProviderError: If the provider is not registered
        StorageError: If there is an error retrieving the data
        SchemaError: If the schema is not registered
        ValidationError: If the data is invalid
        TransformError: If the transform is not registered
        TransformError: If there is an error transforming the data
    """
    # Get the provider
    provider = get_provider(provider_name)

    # Retrieve the data
    data = await provider.retrieve(key)

    # Validate and transform the data if a schema is specified
    if schema_name is not None:
        data = await validate_and_transform(data, schema_name, transform_name)

    return data


async def remove(provider_name: str, key: str) -> None:
    """Remove data.

    Args:
        provider_name: The name of the provider to use
        key: The key to remove the data from

    Raises:
        ProviderError: If the provider is not registered
        StorageError: If there is an error removing the data
    """
    # Get the provider
    provider = get_provider(provider_name)

    # Remove the data
    await provider.remove(key)


async def check(provider_name: str, key: str) -> bool:
    """Check if data exists.

    Args:
        provider_name: The name of the provider to use
        key: The key to check

    Returns:
        True if the data exists, False otherwise

    Raises:
        ProviderError: If the provider is not registered
        StorageError: If there is an error checking the data
    """
    # Get the provider
    provider = get_provider(provider_name)

    # Check if the data exists
    return await provider.exists(key)


async def list_keys(provider_name: str, pattern: Optional[str] = None) -> List[str]:
    """List keys.

    Args:
        provider_name: The name of the provider to use
        pattern: The pattern to match keys against

    Returns:
        A list of keys

    Raises:
        ProviderError: If the provider is not registered
        StorageError: If there is an error listing keys
    """
    # Get the provider
    provider = get_provider(provider_name)

    # List keys
    return await provider.list_keys(pattern)


async def clear_data(provider_name: str) -> None:
    """Clear all data.

    Args:
        provider_name: The name of the provider to use

    Raises:
        ProviderError: If the provider is not registered
        StorageError: If there is an error clearing data
    """
    # Get the provider
    provider = get_provider(provider_name)

    # Clear all data
    await provider.clear()


__all__ = [
    # Errors
    "NetworkError",
    "PepperPyError",
    "QueryError",
    "SchemaError",
    "StorageError",
    "TransformError",
    "ValidationError",
    # Providers
    "Provider",
    "NoSQLProvider",
    "SQLProvider",
    "RESTProvider",
    "CloudProvider",
    "FileProvider",
    # Storage
    "StorageProvider",
    "StorageType",
    "get_provider",
    "list_providers",
    "register_provider",
    "unregister_provider",
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
    "store",
    "retrieve",
    "remove",
    "validate_and_transform",
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
    "DataProvider",
]
