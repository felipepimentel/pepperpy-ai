"""
Storage capability interface.

This module provides the public interface for storage capabilities.
"""

from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from pepperpy.capabilities import CapabilityType
from pepperpy.capabilities.base import BaseCapability, CapabilityConfig


class StorageCapability(BaseCapability):
    """Base class for storage capabilities.

    This class defines the interface that all storage capabilities must implement.
    """

    def __init__(self, config: Optional[CapabilityConfig] = None):
        """Initialize storage capability.

        Args:
            config: Optional configuration for the capability
        """
        super().__init__(CapabilityType.STORAGE, config)

    async def save(self, key: str, data: Union[str, bytes, BinaryIO]) -> str:
        """Save data to storage.

        Args:
            key: Key to store the data under
            data: Data to store

        Returns:
            Storage identifier for the saved data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Storage capability must implement save method")

    async def load(self, key: str) -> Union[str, bytes]:
        """Load data from storage.

        Args:
            key: Key to retrieve

        Returns:
            Retrieved data

        Raises:
            NotImplementedError: If not implemented by subclass
            KeyError: If key doesn't exist
        """
        raise NotImplementedError("Storage capability must implement load method")

    async def delete(self, key: str) -> bool:
        """Delete data from storage.

        Args:
            key: Key to delete

        Returns:
            True if key was deleted, False if key didn't exist

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Storage capability must implement delete method")

    async def exists(self, key: str) -> bool:
        """Check if key exists in storage.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Storage capability must implement exists method")


class FileStorage(StorageCapability):
    """Storage capability for file system operations.

    This class provides methods for storing and retrieving
    data from the file system.
    """

    async def save_file(
        self, file_path: Union[str, Path], data: Union[str, bytes, BinaryIO]
    ) -> str:
        """Save data to a file.

        Args:
            file_path: Path to save the file
            data: Data to save

        Returns:
            Absolute path to the saved file
        """
        pass

    async def load_file(self, file_path: Union[str, Path]) -> bytes:
        """Load data from a file.

        Args:
            file_path: Path to the file

        Returns:
            File contents

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass

    async def list_files(
        self, directory: Union[str, Path], pattern: Optional[str] = None
    ) -> List[str]:
        """List files in a directory.

        Args:
            directory: Directory to list files from
            pattern: Optional glob pattern to filter files

        Returns:
            List of file paths
        """
        pass


class ObjectStorage(StorageCapability):
    """Storage capability for object storage operations.

    This class provides methods for storing and retrieving
    data from object storage systems like S3.
    """

    async def upload(
        self, bucket: str, key: str, data: Union[str, bytes, BinaryIO]
    ) -> str:
        """Upload data to object storage.

        Args:
            bucket: Storage bucket
            key: Object key
            data: Data to upload

        Returns:
            Object URL
        """
        pass

    async def download(self, bucket: str, key: str) -> bytes:
        """Download data from object storage.

        Args:
            bucket: Storage bucket
            key: Object key

        Returns:
            Object data

        Raises:
            KeyError: If object doesn't exist
        """
        pass

    async def list_objects(
        self, bucket: str, prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List objects in a bucket.

        Args:
            bucket: Storage bucket
            prefix: Optional key prefix

        Returns:
            List of object metadata
        """
        pass


# Export public classes
__all__ = [
    "StorageCapability",
    "FileStorage",
    "ObjectStorage",
]
