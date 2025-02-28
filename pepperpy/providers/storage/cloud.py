"""Cloud storage provider implementation."""

from pathlib import Path
from typing import Dict, List, Optional, Union

from pepperpy.storage.base import StorageError, StorageProvider


class CloudStorageProvider(StorageProvider):
    """Cloud storage provider implementation."""

    def __init__(
        self,
        bucket_name: str,
        credentials: Optional[Dict[str, str]] = None,
        project_id: Optional[str] = None,
        **kwargs,
    ):
        """Initialize cloud storage provider.

        Args:
            bucket_name: Cloud storage bucket name
            credentials: Optional service account credentials
            project_id: Optional cloud project ID
            **kwargs: Additional parameters

        Raises:
            ImportError: If google-cloud-storage package is not installed
            StorageError: If initialization fails
        """
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError(
                "google-cloud-storage package is required for CloudStorageProvider. "
                "Install it with: pip install google-cloud-storage"
            )

        self.bucket_name = bucket_name
        self.kwargs = kwargs

        try:
            self.client = storage.Client(
                credentials=credentials,
                project=project_id,
            )
            self.bucket = self.client.bucket(bucket_name)
            if not self.bucket.exists():
                raise StorageError(f"Bucket does not exist: {bucket_name}")
        except Exception as e:
            raise StorageError(f"Failed to initialize cloud storage: {e}")

    def store(self, path: Union[str, Path], data: Union[str, bytes]) -> None:
        """Store data in cloud storage.

        Args:
            path: Path to store data at
            data: Data to store

        Raises:
            StorageError: If storage operation fails
        """
        try:
            blob = self.bucket.blob(str(path))
            if isinstance(data, str):
                blob.upload_from_string(data)
            else:
                blob.upload_from_string(data, content_type="application/octet-stream")
        except Exception as e:
            raise StorageError(f"Failed to store data: {e}")

    def retrieve(self, path: Union[str, Path]) -> bytes:
        """Retrieve data from cloud storage.

        Args:
            path: Path to retrieve data from

        Returns:
            bytes: Retrieved data

        Raises:
            StorageError: If retrieval operation fails
        """
        try:
            blob = self.bucket.blob(str(path))
            if not blob.exists():
                raise StorageError(f"File not found: {path}")
            return blob.download_as_bytes()
        except Exception as e:
            raise StorageError(f"Failed to retrieve data: {e}")

    def delete(self, path: Union[str, Path]) -> bool:
        """Delete file from cloud storage.

        Args:
            path: Path to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            StorageError: If deletion operation fails
        """
        try:
            blob = self.bucket.blob(str(path))
            if not blob.exists():
                return False
            blob.delete()
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete file: {e}")

    def exists(self, path: Union[str, Path]) -> bool:
        """Check if path exists in cloud storage.

        Args:
            path: Path to check

        Returns:
            bool: True if exists, False otherwise

        Raises:
            StorageError: If check operation fails
        """
        try:
            blob = self.bucket.blob(str(path))
            return blob.exists()
        except Exception as e:
            raise StorageError(f"Failed to check path: {e}")

    def list_files(self, path: Optional[Union[str, Path]] = None) -> List[str]:
        """List files in cloud storage.

        Args:
            path: Optional path prefix to list files from

        Returns:
            List[str]: List of file paths

        Raises:
            StorageError: If list operation fails
        """
        try:
            prefix = str(path) if path else None
            blobs = self.bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            raise StorageError(f"Failed to list files: {e}")

    def get_url(self, path: Union[str, Path], expires_in: Optional[int] = None) -> str:
        """Get URL for accessing file in cloud storage.

        Args:
            path: Path to file
            expires_in: Optional expiration time in seconds

        Returns:
            str: URL for accessing file

        Raises:
            StorageError: If URL generation fails
        """
        try:
            blob = self.bucket.blob(str(path))
            if not blob.exists():
                raise StorageError(f"File not found: {path}")
            return blob.generate_signed_url(
                expiration=expires_in,
                **self.kwargs,
            )
        except Exception as e:
            raise StorageError(f"Failed to generate URL: {e}")
