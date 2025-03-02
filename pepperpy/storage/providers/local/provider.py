"""Local storage provider implementation.

This module provides a local filesystem storage provider implementation.
"""

import json
import os
import pickle
from pathlib import Path
from typing import Any, List, Optional, Union

from pepperpy.storage.providers.base.base import BaseStorageProvider
from pepperpy.storage.providers.base.types import StorageProviderType


class LocalStorageProvider(BaseStorageProvider):
    """Local filesystem storage provider implementation."""

    provider_type = StorageProviderType.LOCAL

    def __init__(self, base_path: Union[str, Path], **kwargs):
        """Initialize the local storage provider.

        Args:
            base_path: The base path to store data in.
            **kwargs: Additional configuration options.
        """
        super().__init__(**kwargs)
        self.base_path = Path(base_path)
        os.makedirs(self.base_path, exist_ok=True)

    def _get_full_path(self, key: str) -> Path:
        """Get the full path for a key.

        Args:
            key: The key to get the path for.

        Returns:
            Path: The full path.
        """
        return self.base_path / key

    def save(self, key: str, data: Any) -> bool:
        """Save data to local storage.

        Args:
            key: The key to store the data under.
            data: The data to store.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            path = self._get_full_path(key)
            os.makedirs(path.parent, exist_ok=True)

            # Determine the serialization method based on data type
            if isinstance(data, (dict, list)):
                with open(path, "w") as f:
                    json.dump(data, f)
            else:
                with open(path, "wb") as f:
                    pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"Error saving to local storage: {e}")
            return False

    def load(self, key: str) -> Optional[Any]:
        """Load data from local storage.

        Args:
            key: The key to load data from.

        Returns:
            Optional[Any]: The loaded data, or None if not found.
        """
        try:
            path = self._get_full_path(key)
            if not path.exists():
                return None

            # Try to load as JSON first, then fall back to pickle
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                with open(path, "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading from local storage: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete data from local storage.

        Args:
            key: The key to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            path = self._get_full_path(key)
            if path.exists():
                os.remove(path)
            return True
        except Exception as e:
            print(f"Error deleting from local storage: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in local storage.

        Args:
            key: The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        path = self._get_full_path(key)
        return path.exists()

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys in local storage with the given prefix.

        Args:
            prefix: The prefix to filter keys by.

        Returns:
            List[str]: A list of keys.
        """
        try:
            prefix_path = self.base_path / prefix if prefix else self.base_path
            if not prefix_path.exists():
                return []

            keys = []
            prefix_str = str(prefix_path)
            base_str = str(self.base_path)

            for root, _, files in os.walk(prefix_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    # Convert to relative path from base_path
                    rel_path = os.path.relpath(full_path, base_str)
                    keys.append(rel_path)

            return keys
        except Exception as e:
            print(f"Error listing keys from local storage: {e}")
            return []
