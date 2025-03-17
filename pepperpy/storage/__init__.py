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
    """Storage class for managing data persistence."""

    def __init__(self, provider: StorageProvider[T]):
        """Initialize storage with a provider."""
        self.provider = provider

    def save(self, key: str, data: T) -> None:
        """Save data to storage.

        Args:
            key: The key to save the data under
            data: The data to save

        Raises:
            StorageError: If an error occurs while saving
        """
        try:
            self.provider.save(key, data)
        except Exception as e:
            raise StorageError(f"Error saving data: {str(e)}") from e

    def load(self, key: str) -> Optional[T]:
        """Load data from storage.

        Args:
            key: The key to load the data from

        Returns:
            The loaded data, or None if the key doesn't exist

        Raises:
            StorageError: If an error occurs while loading
        """
        try:
            return self.provider.load(key)
        except Exception as e:
            raise StorageError(f"Error loading data: {str(e)}") from e

    def delete(self, key: str) -> None:
        """Delete data from storage.

        Args:
            key: The key to delete

        Raises:
            StorageError: If an error occurs while deleting
        """
        try:
            self.provider.delete(key)
        except Exception as e:
            raise StorageError(f"Error deleting data: {str(e)}") from e

    def list(self) -> List[str]:
        """List all keys in storage.

        Returns:
            A list of all keys in storage

        Raises:
            StorageError: If an error occurs while listing
        """
        try:
            return self.provider.list()
        except Exception as e:
            raise StorageError(f"Error listing keys: {str(e)}") from e


class MemoryStorage(StorageProvider[T]):
    """In-memory storage provider."""

    def __init__(self):
        """Initialize in-memory storage."""
        self.data: Dict[str, T] = {}

    def save(self, key: str, data: T) -> None:
        """Save data to memory.

        Args:
            key: The key to save the data under
            data: The data to save
        """
        self.data[key] = data

    def load(self, key: str) -> Optional[T]:
        """Load data from memory.

        Args:
            key: The key to load the data from

        Returns:
            The loaded data, or None if the key doesn't exist
        """
        return self.data.get(key)

    def delete(self, key: str) -> None:
        """Delete data from memory.

        Args:
            key: The key to delete
        """
        if key in self.data:
            del self.data[key]

    def list(self) -> List[str]:
        """List all keys in memory.

        Returns:
            A list of all keys in memory
        """
        return list(self.data.keys())


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
        """Get the path for a key.

        Args:
            key: The key to get the path for

        Returns:
            The path for the key
        """
        return os.path.join(self.directory, f"{key}.json")

    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Save data to a file.

        Args:
            key: The key to save the data under
            data: The data to save
        """
        with open(self._get_path(key), "w") as f:
            json.dump(data, f)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data from a file.

        Args:
            key: The key to load the data from

        Returns:
            The loaded data, or None if the file doesn't exist
        """
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def delete(self, key: str) -> None:
        """Delete a file.

        Args:
            key: The key to delete
        """
        path = self._get_path(key)
        if os.path.exists(path):
            os.remove(path)

    def list(self) -> List[str]:
        """List all keys in the directory.

        Returns:
            A list of all keys in the directory
        """
        files = os.listdir(self.directory)
        return [os.path.splitext(f)[0] for f in files if f.endswith(".json")]


__all__ = [
    "Storage",
    "StorageProvider",
    "StorageError",
    "FileStorage",
    "MemoryStorage",
]
