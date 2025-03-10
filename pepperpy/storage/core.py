"""
PepperPy Storage Core Implementation.

This module provides the core implementation of the storage functionality.
"""

import json
import os
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar

from pepperpy.errors import PepperPyError

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
        """Save data to storage."""
        self.provider.save(key, data)

    def load(self, key: str) -> Optional[T]:
        """Load data from storage."""
        return self.provider.load(key)

    def delete(self, key: str) -> None:
        """Delete data from storage."""
        self.provider.delete(key)

    def list(self) -> List[str]:
        """List all keys in storage."""
        return self.provider.list()


class MemoryStorage(StorageProvider[T]):
    """In-memory storage provider."""

    def __init__(self):
        """Initialize in-memory storage."""
        self.data: Dict[str, T] = {}

    def save(self, key: str, data: T) -> None:
        """Save data to memory."""
        self.data[key] = data

    def load(self, key: str) -> Optional[T]:
        """Load data from memory."""
        return self.data.get(key)

    def delete(self, key: str) -> None:
        """Delete data from memory."""
        if key in self.data:
            del self.data[key]

    def list(self) -> List[str]:
        """List all keys in memory."""
        return list(self.data.keys())


class FileStorage(StorageProvider[Dict[str, Any]]):
    """File-based storage provider."""

    def __init__(self, directory: str):
        """Initialize file storage with a directory."""
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _get_path(self, key: str) -> str:
        """Get the file path for a key."""
        return os.path.join(self.directory, f"{key}.json")

    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Save data to a file."""
        path = self._get_path(key)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data from a file."""
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def delete(self, key: str) -> None:
        """Delete a file."""
        path = self._get_path(key)
        if os.path.exists(path):
            os.remove(path)

    def list(self) -> List[str]:
        """List all keys in the directory."""
        files = os.listdir(self.directory)
        return [os.path.splitext(f)[0] for f in files if f.endswith(".json")]
