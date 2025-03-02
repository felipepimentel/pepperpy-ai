"""Base storage provider.

This module defines the base class for all storage providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pepperpy.storage.providers.base.types import StorageProviderType


class BaseStorageProvider(ABC):
    """Base class for all storage providers."""

    provider_type: StorageProviderType

    def __init__(self, **kwargs):
        """Initialize the storage provider."""
        self.config = kwargs

    @abstractmethod
    def save(self, key: str, data: Any) -> bool:
        """Save data to storage.

        Args:
            key: The key to store the data under.
            data: The data to store.

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """Load data from storage.

        Args:
            key: The key to load data from.

        Returns:
            Optional[Any]: The loaded data, or None if not found.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data from storage.

        Args:
            key: The key to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in storage.

        Args:
            key: The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys in storage with the given prefix.

        Args:
            prefix: The prefix to filter keys by.

        Returns:
            List[str]: A list of keys.
        """
        pass
