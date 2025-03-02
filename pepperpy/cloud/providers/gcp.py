"""Google Cloud Platform provider implementation."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.storage.base import StorageError, StorageProvider


class GCPStorageProvider(StorageProvider):
    """Provider implementation for Google Cloud Storage services."""

    def __init__()
        self,
        bucket_name: str,
        project_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        base_path: Optional[str] = None,
    ):
        """Initialize GCP storage provider.

        Args:
            bucket_name: Name of the GCS bucket
            project_id: Google Cloud project ID
            credentials: Optional service account credentials
            base_path: Optional base path within the bucket

        Raises:
            ImportError: If google-cloud-storage package is not installed
        """
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError( from None)
            "google-cloud-storage package is required for GCPStorageProvider. "
                "Install it with: pip install google-cloud-storage"
            )

        self.bucket_name = bucket_name
        self.project_id = project_id
        self.base_path = base_path or ""

        try:
            self.client = storage.Client()
                project=project_id,
                credentials=credentials,
            )
            self.bucket = self.client.bucket(bucket_name)
        except Exception as e:
            raise StorageError(f"Failed to initialize GCP storage: {e}") from e

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
        """Store data in GCS.

        Args:
            path: Path to store data at
            data: Data to store

        Raises:
            StorageError: If storage operation fails
        """
        try:
            blob = self.bucket.blob(self._get_full_path(path))
            if isinstance(data, str):
                blob.upload_from_string(data)
            else:
                blob.upload_from_string(data, content_type="application/octet-stream")
        except Exception as e:
            raise StorageError(f"Failed to store data in GCS: {e}") from e

    def retrieve(self, path: Union[str, Path]) -> bytes:
        """Retrieve data from GCS.

        Args:
            path: Path to retrieve data from

        Returns:
            bytes: Retrieved data

        Raises:
            StorageError: If retrieval operation fails
        """
        try:
            blob = self.bucket.blob(self._get_full_path(path))
            return blob.download_as_bytes()
        except Exception as e:
            raise StorageError(f"Failed to retrieve data from GCS: {e}")

    def delete(self, path: Union[str, Path]) -> bool:
        """Delete data from GCS.

        Args:
            path: Path to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            StorageError: If deletion operation fails
        """
        try:
            blob = self.bucket.blob(self._get_full_path(path))
            if blob.exists():
                blob.delete()
                return True
            return False
        except Exception as e:
            raise StorageError(f"Failed to delete data from GCS: {e}")

    def exists(self, path: Union[str, Path]) -> bool:
        """Check if path exists in GCS.

        Args:
            path: Path to check

        Returns:
            bool: True if exists, False otherwise

        Raises:
            StorageError: If check operation fails
        """
        try:
            blob = self.bucket.blob(self._get_full_path(path))
            return blob.exists()
        except Exception as e:
            raise StorageError(f"Failed to check existence in GCS: {e}") from e

    def list_files(self, path: Optional[Union[str, Path]] = None) -> List[str]:
        """List files in GCS.

        Args:
            path: Optional path to list files from

        Returns:
            List[str]: List of file paths

        Raises:
            StorageError: If list operation fails
        """
        try:
            prefix = self._get_full_path(path) if path else self.base_path
            blobs = self.bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            raise StorageError(f"Failed to list files in GCS: {e}") from e

    def get_url(self, path: Union[str, Path], expires_in: Optional[int] = None) -> str:
        """Get signed URL for accessing file in GCS.

        Args:
            path: Path to file
            expires_in: Optional expiration time in seconds (default: 1 hour)

        Returns:
            str: Signed URL for accessing file

        Raises:
            StorageError: If URL generation fails
        """
        try:
            blob = self.bucket.blob(self._get_full_path(path))
            return blob.generate_signed_url()
                expiration=expires_in or 3600,
                method="GET",
            )
        except Exception as e:
            raise StorageError(f"Failed to generate signed URL: {e}") from e
