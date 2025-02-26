"""Cloud storage provider implementation."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.providers.storage.base import StorageProvider


class CloudStorageProvider(StorageProvider):
    """Base class for cloud storage providers."""

    def __init__(
        self,
        bucket_name: str,
        base_path: Optional[str] = None,
        credentials: Optional[Dict[str, Any]] = None,
    ):
        """Initialize cloud storage provider.

        Args:
            bucket_name: Name of the cloud storage bucket
            base_path: Optional base path within the bucket
            credentials: Optional credentials for authentication
        """
        self.bucket_name = bucket_name
        self.base_path = base_path or ""
        self.credentials = credentials or {}

    def _get_full_path(self, path: Union[str, Path]) -> str:
        """Get full path including base path.

        Args:
            path: Path to file or directory

        Returns:
            str: Full path including base path
        """
        path_str = str(path).strip("/")
        if self.base_path:
            return f"{self.base_path.strip('/')}/{path_str}"
        return path_str

    def store(self, path: Union[str, Path], data: Union[str, bytes]) -> None:
        """Store data in cloud storage.

        Args:
            path: Path to store data at
            data: Data to store

        Raises:
            StorageError: If storage operation fails
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Must be implemented by subclass")

    def retrieve(self, path: Union[str, Path]) -> bytes:
        """Retrieve data from cloud storage.

        Args:
            path: Path to retrieve data from

        Returns:
            bytes: Retrieved data

        Raises:
            StorageError: If retrieval operation fails
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Must be implemented by subclass")

    def delete(self, path: Union[str, Path]) -> bool:
        """Delete data from cloud storage.

        Args:
            path: Path to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            StorageError: If deletion operation fails
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Must be implemented by subclass")

    def exists(self, path: Union[str, Path]) -> bool:
        """Check if path exists in cloud storage.

        Args:
            path: Path to check

        Returns:
            bool: True if exists, False otherwise

        Raises:
            StorageError: If check operation fails
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Must be implemented by subclass")

    def list_files(self, path: Optional[Union[str, Path]] = None) -> List[str]:
        """List files in cloud storage.

        Args:
            path: Optional path to list files from

        Returns:
            List[str]: List of file paths

        Raises:
            StorageError: If list operation fails
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Must be implemented by subclass")

    def get_url(self, path: Union[str, Path], expires_in: Optional[int] = None) -> str:
        """Get URL for accessing file in cloud storage.

        Args:
            path: Path to file
            expires_in: Optional expiration time in seconds

        Returns:
            str: URL for accessing file

        Raises:
            StorageError: If URL generation fails
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Must be implemented by subclass")
