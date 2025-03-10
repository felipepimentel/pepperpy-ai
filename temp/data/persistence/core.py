"""Core functionality for data persistence.

This module provides the core functionality for data persistence,
including storage providers and data access.
"""

import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.data.errors import ConnectionError, PersistenceError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for data types
T = TypeVar("T")
U = TypeVar("U")


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
    async def get(self, key: str) -> Any:
        """Get data from the storage.

        Args:
            key: The key to get

        Returns:
            The data

        Raises:
            PersistenceError: If there is an error getting the data
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """Set data in the storage.

        Args:
            key: The key to set
            value: The value to set

        Raises:
            PersistenceError: If there is an error setting the data
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete data from the storage.

        Args:
            key: The key to delete

        Raises:
            PersistenceError: If there is an error deleting the data
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the storage.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise

        Raises:
            PersistenceError: If there is an error checking if the key exists
        """
        pass

    @abstractmethod
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get keys from the storage.

        Args:
            pattern: The pattern to match

        Returns:
            The keys

        Raises:
            PersistenceError: If there is an error getting the keys
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear the storage.

        Raises:
            PersistenceError: If there is an error clearing the storage
        """
        pass


class MemoryStorageProvider(StorageProvider):
    """Storage provider that stores data in memory.

    This provider stores data in memory.
    """

    def __init__(self, name: str):
        """Initialize a memory storage provider.

        Args:
            name: The name of the provider
        """
        self._name = name
        self._data: Dict[str, Any] = {}
        self._connected = False

    @property
    def name(self) -> str:
        """Get the name of the provider.

        Returns:
            The name of the provider
        """
        return self._name

    @property
    def storage_type(self) -> StorageType:
        """Get the type of storage.

        Returns:
            The type of storage
        """
        return StorageType.MEMORY

    async def connect(self) -> None:
        """Connect to the storage.

        Raises:
            ConnectionError: If there is an error connecting to the storage
        """
        self._connected = True

    async def disconnect(self) -> None:
        """Disconnect from the storage.

        Raises:
            ConnectionError: If there is an error disconnecting from the storage
        """
        self._connected = False

    async def is_connected(self) -> bool:
        """Check if the provider is connected.

        Returns:
            True if the provider is connected, False otherwise
        """
        return self._connected

    async def get(self, key: str) -> Any:
        """Get data from the storage.

        Args:
            key: The key to get

        Returns:
            The data

        Raises:
            PersistenceError: If there is an error getting the data
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        if key not in self._data:
            raise PersistenceError(f"Key '{key}' not found")

        return self._data[key]

    async def set(self, key: str, value: Any) -> None:
        """Set data in the storage.

        Args:
            key: The key to set
            value: The value to set

        Raises:
            PersistenceError: If there is an error setting the data
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        self._data[key] = value

    async def delete(self, key: str) -> None:
        """Delete data from the storage.

        Args:
            key: The key to delete

        Raises:
            PersistenceError: If there is an error deleting the data
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        if key not in self._data:
            raise PersistenceError(f"Key '{key}' not found")

        del self._data[key]

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the storage.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise

        Raises:
            PersistenceError: If there is an error checking if the key exists
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        return key in self._data

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get keys from the storage.

        Args:
            pattern: The pattern to match

        Returns:
            The keys

        Raises:
            PersistenceError: If there is an error getting the keys
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        if pattern is None:
            return list(self._data.keys())

        import re

        regex = re.compile(pattern)
        return [key for key in self._data.keys() if regex.match(key)]

    async def clear(self) -> None:
        """Clear the storage.

        Raises:
            PersistenceError: If there is an error clearing the storage
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        self._data.clear()


class FileStorageProvider(StorageProvider):
    """Storage provider that stores data in a file.

    This provider stores data in a file.
    """

    def __init__(self, name: str, file_path: str):
        """Initialize a file storage provider.

        Args:
            name: The name of the provider
            file_path: The path to the file
        """
        self._name = name
        self._file_path = file_path
        self._data: Dict[str, Any] = {}
        self._connected = False

    @property
    def name(self) -> str:
        """Get the name of the provider.

        Returns:
            The name of the provider
        """
        return self._name

    @property
    def storage_type(self) -> StorageType:
        """Get the type of storage.

        Returns:
            The type of storage
        """
        return StorageType.FILE

    async def connect(self) -> None:
        """Connect to the storage.

        Raises:
            ConnectionError: If there is an error connecting to the storage
        """
        try:
            import os

            import aiofiles

            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)

            # Load the data if the file exists
            if os.path.exists(self._file_path):
                async with aiofiles.open(self._file_path, "r") as f:
                    content = await f.read()
                    if content:
                        self._data = json.loads(content)

            self._connected = True
        except Exception as e:
            raise ConnectionError(f"Error connecting to file: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the storage.

        Raises:
            ConnectionError: If there is an error disconnecting from the storage
        """
        try:
            import aiofiles

            # Save the data
            async with aiofiles.open(self._file_path, "w") as f:
                await f.write(json.dumps(self._data))

            self._connected = False
        except Exception as e:
            raise ConnectionError(f"Error disconnecting from file: {e}")

    async def is_connected(self) -> bool:
        """Check if the provider is connected.

        Returns:
            True if the provider is connected, False otherwise
        """
        return self._connected

    async def get(self, key: str) -> Any:
        """Get data from the storage.

        Args:
            key: The key to get

        Returns:
            The data

        Raises:
            PersistenceError: If there is an error getting the data
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        if key not in self._data:
            raise PersistenceError(f"Key '{key}' not found")

        return self._data[key]

    async def set(self, key: str, value: Any) -> None:
        """Set data in the storage.

        Args:
            key: The key to set
            value: The value to set

        Raises:
            PersistenceError: If there is an error setting the data
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        self._data[key] = value

        # Save the data
        try:
            import aiofiles

            async with aiofiles.open(self._file_path, "w") as f:
                await f.write(json.dumps(self._data))
        except Exception as e:
            raise PersistenceError(f"Error saving data: {e}")

    async def delete(self, key: str) -> None:
        """Delete data from the storage.

        Args:
            key: The key to delete

        Raises:
            PersistenceError: If there is an error deleting the data
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        if key not in self._data:
            raise PersistenceError(f"Key '{key}' not found")

        del self._data[key]

        # Save the data
        try:
            import aiofiles

            async with aiofiles.open(self._file_path, "w") as f:
                await f.write(json.dumps(self._data))
        except Exception as e:
            raise PersistenceError(f"Error saving data: {e}")

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the storage.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise

        Raises:
            PersistenceError: If there is an error checking if the key exists
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        return key in self._data

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get keys from the storage.

        Args:
            pattern: The pattern to match

        Returns:
            The keys

        Raises:
            PersistenceError: If there is an error getting the keys
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        if pattern is None:
            return list(self._data.keys())

        import re

        regex = re.compile(pattern)
        return [key for key in self._data.keys() if regex.match(key)]

    async def clear(self) -> None:
        """Clear the storage.

        Raises:
            PersistenceError: If there is an error clearing the storage
        """
        if not self._connected:
            raise ConnectionError("Provider is not connected")

        self._data.clear()

        # Save the data
        try:
            import aiofiles

            async with aiofiles.open(self._file_path, "w") as f:
                await f.write(json.dumps(self._data))
        except Exception as e:
            raise PersistenceError(f"Error saving data: {e}")


class StorageProviderRegistry:
    """Registry for storage providers.

    The storage provider registry is responsible for managing storage providers.
    """

    def __init__(self):
        """Initialize a storage provider registry."""
        self._providers: Dict[str, StorageProvider] = {}

    def register(self, provider: StorageProvider) -> None:
        """Register a storage provider.

        Args:
            provider: The storage provider to register

        Raises:
            PersistenceError: If a storage provider with the same name is already registered
        """
        if provider.name in self._providers:
            raise PersistenceError(f"Provider '{provider.name}' is already registered")

        self._providers[provider.name] = provider

    def unregister(self, name: str) -> None:
        """Unregister a storage provider.

        Args:
            name: The name of the storage provider to unregister

        Raises:
            PersistenceError: If the storage provider is not registered
        """
        if name not in self._providers:
            raise PersistenceError(f"Provider '{name}' is not registered")

        del self._providers[name]

    def get(self, name: str) -> StorageProvider:
        """Get a storage provider by name.

        Args:
            name: The name of the storage provider

        Returns:
            The storage provider

        Raises:
            PersistenceError: If the storage provider is not registered
        """
        if name not in self._providers:
            raise PersistenceError(f"Provider '{name}' is not registered")

        return self._providers[name]

    def list(self) -> List[str]:
        """List all registered storage providers.

        Returns:
            The names of all registered storage providers
        """
        return list(self._providers.keys())

    def clear(self) -> None:
        """Clear all registered storage providers."""
        self._providers.clear()


# Default storage provider registry
_registry = StorageProviderRegistry()


def get_registry() -> StorageProviderRegistry:
    """Get the default storage provider registry.

    Returns:
        The default storage provider registry
    """
    return _registry


def set_registry(registry: StorageProviderRegistry) -> None:
    """Set the default storage provider registry.

    Args:
        registry: The storage provider registry to set as the default
    """
    global _registry
    _registry = registry


def register_provider(provider: StorageProvider) -> None:
    """Register a storage provider in the default registry.

    Args:
        provider: The storage provider to register

    Raises:
        PersistenceError: If a storage provider with the same name is already registered
    """
    get_registry().register(provider)


def unregister_provider(name: str) -> None:
    """Unregister a storage provider from the default registry.

    Args:
        name: The name of the storage provider to unregister

    Raises:
        PersistenceError: If the storage provider is not registered
    """
    get_registry().unregister(name)


def get_provider(name: str) -> StorageProvider:
    """Get a storage provider by name from the default registry.

    Args:
        name: The name of the storage provider

    Returns:
        The storage provider

    Raises:
        PersistenceError: If the storage provider is not registered
    """
    return get_registry().get(name)


def list_providers() -> List[str]:
    """List all registered storage providers in the default registry.

    Returns:
        The names of all registered storage providers
    """
    return get_registry().list()


def clear_providers() -> None:
    """Clear all registered storage providers in the default registry."""
    get_registry().clear()


def register_memory_provider(name: str) -> None:
    """Register a memory storage provider.

    Args:
        name: The name of the provider

    Raises:
        PersistenceError: If a storage provider with the same name is already registered
    """
    provider = MemoryStorageProvider(name)
    register_provider(provider)


def register_file_provider(name: str, file_path: str) -> None:
    """Register a file storage provider.

    Args:
        name: The name of the provider
        file_path: The path to the file

    Raises:
        PersistenceError: If a storage provider with the same name is already registered
    """
    provider = FileStorageProvider(name, file_path)
    register_provider(provider)


async def connect(name: str) -> None:
    """Connect to a storage provider.

    Args:
        name: The name of the storage provider

    Raises:
        PersistenceError: If the storage provider is not registered
        ConnectionError: If there is an error connecting to the storage
    """
    provider = get_provider(name)
    await provider.connect()


async def disconnect(name: str) -> None:
    """Disconnect from a storage provider.

    Args:
        name: The name of the storage provider

    Raises:
        PersistenceError: If the storage provider is not registered
        ConnectionError: If there is an error disconnecting from the storage
    """
    provider = get_provider(name)
    await provider.disconnect()


async def is_connected(name: str) -> bool:
    """Check if a storage provider is connected.

    Args:
        name: The name of the storage provider

    Returns:
        True if the storage provider is connected, False otherwise

    Raises:
        PersistenceError: If the storage provider is not registered
    """
    provider = get_provider(name)
    return await provider.is_connected()


async def get(name: str, key: str) -> Any:
    """Get data from a storage provider.

    Args:
        name: The name of the storage provider
        key: The key to get

    Returns:
        The data

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error getting the data
    """
    provider = get_provider(name)
    return await provider.get(key)


async def set(name: str, key: str, value: Any) -> None:
    """Set data in a storage provider.

    Args:
        name: The name of the storage provider
        key: The key to set
        value: The value to set

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error setting the data
    """
    provider = get_provider(name)
    await provider.set(key, value)


async def delete(name: str, key: str) -> None:
    """Delete data from a storage provider.

    Args:
        name: The name of the storage provider
        key: The key to delete

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error deleting the data
    """
    provider = get_provider(name)
    await provider.delete(key)


async def exists(name: str, key: str) -> bool:
    """Check if a key exists in a storage provider.

    Args:
        name: The name of the storage provider
        key: The key to check

    Returns:
        True if the key exists, False otherwise

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error checking if the key exists
    """
    provider = get_provider(name)
    return await provider.exists(key)


async def keys(name: str, pattern: Optional[str] = None) -> List[str]:
    """Get keys from a storage provider.

    Args:
        name: The name of the storage provider
        pattern: The pattern to match

    Returns:
        The keys

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error getting the keys
    """
    provider = get_provider(name)
    return await provider.keys(pattern)


async def clear(name: str) -> None:
    """Clear a storage provider.

    Args:
        name: The name of the storage provider

    Raises:
        PersistenceError: If the storage provider is not registered
        PersistenceError: If there is an error clearing the storage
    """
    provider = get_provider(name)
    await provider.clear()
