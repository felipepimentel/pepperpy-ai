"""Persistence module.

This module provides functionality for data persistence.
"""

import json
import os
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.errors import PepperPyError


class StorageError(PepperPyError):
    """Error raised when a storage operation fails."""

    pass


class StorageType(Enum):
    """Types of storage providers."""

    MEMORY = auto()
    FILE = auto()
    DATABASE = auto()
    CLOUD = auto()


class StorageProvider:
    """Base class for storage providers."""

    def __init__(self, provider_id: str, provider_type: StorageType):
        """Initialize a storage provider.

        Args:
            provider_id: The ID of the provider
            provider_type: The type of the provider
        """
        self.provider_id = provider_id
        self.provider_type = provider_type
        self._connected = False

    async def connect(self) -> None:
        """Connect to the storage.

        Raises:
            StorageError: If connection fails
        """
        self._connected = True

    async def disconnect(self) -> None:
        """Disconnect from the storage.

        Raises:
            StorageError: If disconnection fails
        """
        self._connected = False

    def is_connected(self) -> bool:
        """Check if the provider is connected.

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    async def get(self, key: str) -> Any:
        """Get a value from storage.

        Args:
            key: The key to get

        Returns:
            The value, or None if not found

        Raises:
            StorageError: If the operation fails
        """
        raise StorageError("Not implemented")

    async def set(self, key: str, value: Any) -> None:
        """Set a value in storage.

        Args:
            key: The key to set
            value: The value to set

        Raises:
            StorageError: If the operation fails
        """
        raise StorageError("Not implemented")

    async def delete(self, key: str) -> None:
        """Delete a value from storage.

        Args:
            key: The key to delete

        Raises:
            StorageError: If the operation fails
        """
        raise StorageError("Not implemented")

    async def exists(self, key: str) -> bool:
        """Check if a key exists in storage.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise

        Raises:
            StorageError: If the operation fails
        """
        raise StorageError("Not implemented")

    async def keys(self) -> List[str]:
        """Get all keys in storage.

        Returns:
            A list of all keys

        Raises:
            StorageError: If the operation fails
        """
        raise StorageError("Not implemented")

    async def clear(self) -> None:
        """Clear all data in storage.

        Raises:
            StorageError: If the operation fails
        """
        raise StorageError("Not implemented")


class MemoryStorageProvider(StorageProvider):
    """In-memory storage provider."""

    def __init__(self, provider_id: str = "memory"):
        """Initialize a memory storage provider.

        Args:
            provider_id: The ID of the provider
        """
        super().__init__(provider_id, StorageType.MEMORY)
        self._data: Dict[str, Any] = {}

    async def get(self, key: str) -> Any:
        """Get a value from storage.

        Args:
            key: The key to get

        Returns:
            The value, or None if not found

        Raises:
            StorageError: If the operation fails
        """
        return self._data.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Set a value in storage.

        Args:
            key: The key to set
            value: The value to set

        Raises:
            StorageError: If the operation fails
        """
        self._data[key] = value

    async def delete(self, key: str) -> None:
        """Delete a value from storage.

        Args:
            key: The key to delete

        Raises:
            StorageError: If the operation fails
        """
        if key in self._data:
            del self._data[key]

    async def exists(self, key: str) -> bool:
        """Check if a key exists in storage.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise

        Raises:
            StorageError: If the operation fails
        """
        return key in self._data

    async def keys(self) -> List[str]:
        """Get all keys in storage.

        Returns:
            A list of all keys

        Raises:
            StorageError: If the operation fails
        """
        return list(self._data.keys())

    async def clear(self) -> None:
        """Clear all data in storage.

        Raises:
            StorageError: If the operation fails
        """
        self._data.clear()


class FileStorageProvider(StorageProvider):
    """File-based storage provider."""

    def __init__(
        self, provider_id: str = "file", base_path: Optional[Union[str, Path]] = None
    ):
        """Initialize a file storage provider.

        Args:
            provider_id: The ID of the provider
            base_path: The base path for storage files
        """
        super().__init__(provider_id, StorageType.FILE)
        self.base_path = Path(base_path or os.path.expanduser("~/.pepperpy/storage"))

    async def connect(self) -> None:
        """Connect to the storage.

        Raises:
            StorageError: If connection fails
        """
        try:
            os.makedirs(self.base_path, exist_ok=True)
            await super().connect()
        except Exception as e:
            raise StorageError(f"Failed to connect to file storage: {str(e)}")

    async def get(self, key: str) -> Any:
        """Get a value from storage.

        Args:
            key: The key to get

        Returns:
            The value, or None if not found

        Raises:
            StorageError: If the operation fails
        """
        file_path = self.base_path / f"{key}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise StorageError(f"Failed to get value for key {key}: {str(e)}")

    async def set(self, key: str, value: Any) -> None:
        """Set a value in storage.

        Args:
            key: The key to set
            value: The value to set

        Raises:
            StorageError: If the operation fails
        """
        file_path = self.base_path / f"{key}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2)
        except Exception as e:
            raise StorageError(f"Failed to set value for key {key}: {str(e)}")

    async def delete(self, key: str) -> None:
        """Delete a value from storage.

        Args:
            key: The key to delete

        Raises:
            StorageError: If the operation fails
        """
        file_path = self.base_path / f"{key}.json"
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception as e:
                raise StorageError(f"Failed to delete key {key}: {str(e)}")

    async def exists(self, key: str) -> bool:
        """Check if a key exists in storage.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise

        Raises:
            StorageError: If the operation fails
        """
        file_path = self.base_path / f"{key}.json"
        return file_path.exists()

    async def keys(self) -> List[str]:
        """Get all keys in storage.

        Returns:
            A list of all keys

        Raises:
            StorageError: If the operation fails
        """
        try:
            keys = []
            for file_path in self.base_path.glob("*.json"):
                keys.append(file_path.stem)
            return keys
        except Exception as e:
            raise StorageError(f"Failed to get keys: {str(e)}")

    async def clear(self) -> None:
        """Clear all data in storage.

        Raises:
            StorageError: If the operation fails
        """
        try:
            for file_path in self.base_path.glob("*.json"):
                os.remove(file_path)
        except Exception as e:
            raise StorageError(f"Failed to clear storage: {str(e)}")


class StorageProviderRegistry:
    """Registry for storage providers."""

    def __init__(self):
        """Initialize the registry."""
        self._providers: Dict[str, StorageProvider] = {}
        self._default_provider: Optional[str] = None

    def register_provider(self, provider: StorageProvider) -> None:
        """Register a storage provider.

        Args:
            provider: The provider to register

        Raises:
            StorageError: If a provider with the same ID is already registered
        """
        if provider.provider_id in self._providers:
            raise StorageError(f"Provider {provider.provider_id} already registered")
        self._providers[provider.provider_id] = provider

        # Set as default if it's the first provider
        if self._default_provider is None:
            self._default_provider = provider.provider_id

    def get_provider(self, provider_id: Optional[str] = None) -> StorageProvider:
        """Get a storage provider.

        Args:
            provider_id: The ID of the provider, or None for the default provider

        Returns:
            The storage provider

        Raises:
            StorageError: If the provider is not found
        """
        if provider_id is None:
            if self._default_provider is None:
                raise StorageError("No default provider set")
            provider_id = self._default_provider

        if provider_id not in self._providers:
            raise StorageError(f"Provider {provider_id} not found")

        return self._providers[provider_id]

    def unregister_provider(self, provider_id: str) -> None:
        """Unregister a storage provider.

        Args:
            provider_id: The ID of the provider to unregister
        """
        if provider_id in self._providers:
            del self._providers[provider_id]

            # Update default provider if needed
            if self._default_provider == provider_id:
                self._default_provider = (
                    next(iter(self._providers.keys())) if self._providers else None
                )

    def list_providers(self) -> List[str]:
        """List all registered provider IDs.

        Returns:
            A list of all registered provider IDs
        """
        return list(self._providers.keys())

    def clear_providers(self) -> None:
        """Clear all registered providers."""
        self._providers.clear()
        self._default_provider = None


# Global registry instance
_registry = StorageProviderRegistry()


def register_provider(provider: StorageProvider) -> None:
    """Register a storage provider.

    Args:
        provider: The provider to register

    Raises:
        StorageError: If a provider with the same ID is already registered
    """
    _registry.register_provider(provider)


def register_memory_provider(provider_id: str = "memory") -> StorageProvider:
    """Register a memory storage provider.

    Args:
        provider_id: The ID of the provider

    Returns:
        The registered provider

    Raises:
        StorageError: If a provider with the same ID is already registered
    """
    provider = MemoryStorageProvider(provider_id)
    register_provider(provider)
    return provider


def register_file_provider(
    provider_id: str = "file", base_path: Optional[Union[str, Path]] = None
) -> StorageProvider:
    """Register a file storage provider.

    Args:
        provider_id: The ID of the provider
        base_path: The base path for storage files

    Returns:
        The registered provider

    Raises:
        StorageError: If a provider with the same ID is already registered
    """
    provider = FileStorageProvider(provider_id, base_path)
    register_provider(provider)
    return provider


def get_provider(provider_id: Optional[str] = None) -> StorageProvider:
    """Get a storage provider.

    Args:
        provider_id: The ID of the provider, or None for the default provider

    Returns:
        The storage provider

    Raises:
        StorageError: If the provider is not found
    """
    return _registry.get_provider(provider_id)


def unregister_provider(provider_id: str) -> None:
    """Unregister a storage provider.

    Args:
        provider_id: The ID of the provider to unregister
    """
    _registry.unregister_provider(provider_id)


def list_providers() -> List[str]:
    """List all registered provider IDs.

    Returns:
        A list of all registered provider IDs
    """
    return _registry.list_providers()


def clear_providers() -> None:
    """Clear all registered providers."""
    _registry.clear_providers()


def get_registry() -> StorageProviderRegistry:
    """Get the global registry instance.

    Returns:
        The global registry instance
    """
    return _registry


def set_registry(registry: StorageProviderRegistry) -> None:
    """Set the global registry instance.

    Args:
        registry: The registry instance to set
    """
    global _registry
    _registry = registry


async def connect(provider_id: Optional[str] = None) -> None:
    """Connect to a storage provider.

    Args:
        provider_id: The ID of the provider, or None for the default provider

    Raises:
        StorageError: If connection fails
    """
    provider = get_provider(provider_id)
    await provider.connect()


async def disconnect(provider_id: Optional[str] = None) -> None:
    """Disconnect from a storage provider.

    Args:
        provider_id: The ID of the provider, or None for the default provider

    Raises:
        StorageError: If disconnection fails
    """
    provider = get_provider(provider_id)
    await provider.disconnect()


def is_connected(provider_id: Optional[str] = None) -> bool:
    """Check if a provider is connected.

    Args:
        provider_id: The ID of the provider, or None for the default provider

    Returns:
        True if connected, False otherwise

    Raises:
        StorageError: If the provider is not found
    """
    provider = get_provider(provider_id)
    return provider.is_connected()


async def get(key: str, provider_id: Optional[str] = None) -> Any:
    """Get a value from storage.

    Args:
        key: The key to get
        provider_id: The ID of the provider, or None for the default provider

    Returns:
        The value, or None if not found

    Raises:
        StorageError: If the operation fails
    """
    provider = get_provider(provider_id)
    return await provider.get(key)


async def set(key: str, value: Any, provider_id: Optional[str] = None) -> None:
    """Set a value in storage.

    Args:
        key: The key to set
        value: The value to set
        provider_id: The ID of the provider, or None for the default provider

    Raises:
        StorageError: If the operation fails
    """
    provider = get_provider(provider_id)
    await provider.set(key, value)


async def delete(key: str, provider_id: Optional[str] = None) -> None:
    """Delete a value from storage.

    Args:
        key: The key to delete
        provider_id: The ID of the provider, or None for the default provider

    Raises:
        StorageError: If the operation fails
    """
    provider = get_provider(provider_id)
    await provider.delete(key)


async def exists(key: str, provider_id: Optional[str] = None) -> bool:
    """Check if a key exists in storage.

    Args:
        key: The key to check
        provider_id: The ID of the provider, or None for the default provider

    Returns:
        True if the key exists, False otherwise

    Raises:
        StorageError: If the operation fails
    """
    provider = get_provider(provider_id)
    return await provider.exists(key)


async def keys(provider_id: Optional[str] = None) -> List[str]:
    """Get all keys in storage.

    Args:
        provider_id: The ID of the provider, or None for the default provider

    Returns:
        A list of all keys

    Raises:
        StorageError: If the operation fails
    """
    provider = get_provider(provider_id)
    return await provider.keys()


async def clear(provider_id: Optional[str] = None) -> None:
    """Clear all data in storage.

    Args:
        provider_id: The ID of the provider, or None for the default provider

    Raises:
        StorageError: If the operation fails
    """
    provider = get_provider(provider_id)
    await provider.clear()


__all__ = [
    "StorageError",
    "StorageType",
    "StorageProvider",
    "MemoryStorageProvider",
    "FileStorageProvider",
    "StorageProviderRegistry",
    "register_provider",
    "register_memory_provider",
    "register_file_provider",
    "get_provider",
    "unregister_provider",
    "list_providers",
    "clear_providers",
    "get_registry",
    "set_registry",
    "connect",
    "disconnect",
    "is_connected",
    "get",
    "set",
    "delete",
    "exists",
    "keys",
    "clear",
]
