"""Core functionality for data module.

This module provides the core functionality for data handling,
including schema validation, data transformation, and persistence.
"""

from typing import Any, List, Optional, TypeVar

from pepperpy.data.persistence.core import get_provider
from pepperpy.data.schema.core import validate
from pepperpy.data.transform.core import transform
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for data types
T = TypeVar("T")


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
        provider_name: The name of the storage provider
        key: The key to store the data under
        schema_name: The name of the schema to validate against
        transform_name: The name of the transform to apply

    Raises:
        SchemaError: If the schema is not registered
        ValidationError: If the data is invalid
        TransformError: If the transform is not registered
        TransformError: If there is an error transforming the data
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error storing the data
    """
    # Validate and transform the data if a schema or transform is specified
    if schema_name is not None or transform_name is not None:
        data = await validate_and_transform(data, schema_name or "", transform_name)

    # Store the data
    provider = get_provider(provider_name)
    await provider.set(key, data)


async def retrieve(
    provider_name: str,
    key: str,
    schema_name: Optional[str] = None,
    transform_name: Optional[str] = None,
) -> Any:
    """Retrieve data.

    Args:
        provider_name: The name of the storage provider
        key: The key to retrieve the data from
        schema_name: The name of the schema to validate against
        transform_name: The name of the transform to apply

    Returns:
        The retrieved data

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error retrieving the data
        SchemaError: If the schema is not registered
        ValidationError: If the data is invalid
        TransformError: If the transform is not registered
        TransformError: If there is an error transforming the data
    """
    # Retrieve the data
    provider = get_provider(provider_name)
    data = await provider.get(key)

    # Validate and transform the data if a schema or transform is specified
    if schema_name is not None or transform_name is not None:
        data = await validate_and_transform(data, schema_name or "", transform_name)

    return data


async def remove(provider_name: str, key: str) -> None:
    """Remove data.

    Args:
        provider_name: The name of the storage provider
        key: The key to remove the data from

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error removing the data
    """
    # Remove the data
    provider = get_provider(provider_name)
    await provider.delete(key)


async def check(provider_name: str, key: str) -> bool:
    """Check if data exists.

    Args:
        provider_name: The name of the storage provider
        key: The key to check

    Returns:
        True if the data exists, False otherwise

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error checking if the data exists
    """
    # Check if the data exists
    provider = get_provider(provider_name)
    return await provider.exists(key)


async def list_keys(provider_name: str, pattern: Optional[str] = None) -> List[str]:
    """List keys.

    Args:
        provider_name: The name of the storage provider
        pattern: The pattern to match

    Returns:
        The keys

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error listing the keys
    """
    # List the keys
    provider = get_provider(provider_name)
    return await provider.keys(pattern)


async def clear_data(provider_name: str) -> None:
    """Clear data.

    Args:
        provider_name: The name of the storage provider

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error clearing the data
    """
    # Clear the data
    provider = get_provider(provider_name)
    await provider.clear()
