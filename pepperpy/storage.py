"""
PepperPy Storage Module.

This module provides storage functionality for the PepperPy framework.
"""

import json
import os
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar

from pepperpy.core.errors import PepperPyError

T = TypeVar("T")


class StorageError(PepperPyError):
    """Base class for storage errors."""

    pass


class StorageProvider(Protocol, Generic[T]):
    """Protocol for storage providers."""

    def save(self, key: str, data: T) -> None:
        """Save data to storage."""
        ...

    def load(self, key: str) -> Optional[T]:
        """Load data from storage."""
        ...

    def delete(self, key: str) -> None:
        """Delete data from storage."""
        ...

    def list(self) -> List[str]:
        """List all keys in storage."""
        ...


class Storage(Generic[T]):
    """Generic storage class."""

    def __init__(self, provider: StorageProvider[T]):
        """Initialize storage with a provider."""
        self.provider = provider

    def save(self, key: str, data: T) -> None:
        """Save data to storage.

        Args:
            key: The key to save the data under
            data: The data to save

        Raises:
            StorageError: If the data cannot be saved
        """
        try:
            self.provider.save(key, data)
        except Exception as e:
            raise StorageError(f"Failed to save data: {str(e)}") from e

    def load(self, key: str) -> Optional[T]:
        """Load data from storage.

        Args:
            key: The key to load the data from

        Returns:
            The loaded data, or None if the key does not exist

        Raises:
            StorageError: If the data cannot be loaded
        """
        try:
            return self.provider.load(key)
        except Exception as e:
            raise StorageError(f"Failed to load data: {str(e)}") from e

    def delete(self, key: str) -> None:
        """Delete data from storage.

        Args:
            key: The key to delete

        Raises:
            StorageError: If the data cannot be deleted
        """
        try:
            self.provider.delete(key)
        except Exception as e:
            raise StorageError(f"Failed to delete data: {str(e)}") from e

    def list(self) -> List[str]:
        """List all keys in storage.

        Returns:
            A list of all keys in storage

        Raises:
            StorageError: If the keys cannot be listed
        """
        try:
            return self.provider.list()
        except Exception as e:
            raise StorageError(f"Failed to list keys: {str(e)}") from e


class MemoryStorage(StorageProvider[T]):
    """In-memory storage provider."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._data: Dict[str, T] = {}

    def save(self, key: str, data: T) -> None:
        """Save data to storage.

        Args:
            key: The key to save the data under
            data: The data to save
        """
        self._data[key] = data

    def load(self, key: str) -> Optional[T]:
        """Load data from storage.

        Args:
            key: The key to load the data from

        Returns:
            The loaded data, or None if the key does not exist
        """
        return self._data.get(key)

    def delete(self, key: str) -> None:
        """Delete data from storage.

        Args:
            key: The key to delete
        """
        if key in self._data:
            del self._data[key]

    def list(self) -> List[str]:
        """List all keys in storage.

        Returns:
            A list of all keys in storage
        """
        return list(self._data.keys())


class FileStorage(StorageProvider[Dict[str, Any]]):
    """File-based storage provider."""

    def __init__(self, directory: str):
        """Initialize file-based storage.

        Args:
            directory: The directory to store files in
        """
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _get_path(self, key: str) -> str:
        """Get the file path for a key.

        Args:
            key: The key to get the path for

        Returns:
            The file path for the key
        """
        # Ensure the key is a valid filename
        safe_key = key.replace("/", "_").replace("\\", "_")
        return os.path.join(self.directory, f"{safe_key}.json")

    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Save data to storage.

        Args:
            key: The key to save the data under
            data: The data to save
        """
        with open(self._get_path(key), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data from storage.

        Args:
            key: The key to load the data from

        Returns:
            The loaded data, or None if the key does not exist
        """
        path = self._get_path(key)
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete(self, key: str) -> None:
        """Delete data from storage.

        Args:
            key: The key to delete
        """
        path = self._get_path(key)
        if os.path.exists(path):
            os.remove(path)

    def list(self) -> List[str]:
        """List all keys in storage.

        Returns:
            A list of all keys in storage
        """
        files = [f for f in os.listdir(self.directory) if f.endswith(".json")]
        return [f[:-5] for f in files]  # Remove .json extension


def create_memory_storage() -> MemoryStorage[Any]:
    """Create a memory storage provider.

    Returns:
        A memory storage provider
    """
    return MemoryStorage()


def create_file_storage(directory: str) -> FileStorage:
    """Create a file storage provider.

    Args:
        directory: The directory to store files in

    Returns:
        A file storage provider
    """
    return FileStorage(directory)


__all__ = [
    "StorageError",
    "StorageProvider",
    "Storage",
    "MemoryStorage",
    "FileStorage",
    "create_memory_storage",
    "create_file_storage",
]
