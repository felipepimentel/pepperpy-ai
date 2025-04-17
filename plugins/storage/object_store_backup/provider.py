"""Object Store Module.

This module provides a high-level interface for object storage operations,
abstracting away the underlying storage provider implementation.

Example:
    >>> from pepperpy.storage import ObjectStore, StorageProvider
    >>> provider = StorageProvider.from_config({
    ...     "provider": "local",
    ...     "path": "/tmp/storage"
    ... })
    >>> store = ObjectStore(provider)
    >>> store.put("config", {"debug": True})
    >>> config = store.get("config")
    >>> assert config["debug"] is True
"""

import base64
import hashlib
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aioboto3
import httpx

from pepperpy.core import ProviderError, ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugin.plugin import PepperpyPlugin


class PersistenceError(ProviderError):
    """Exception raised for persistence-related errors."""

    pass


class StorageError(ProviderError):
    """Exception raised for storage-related errors."""

    pass


class StorageProvider(PepperpyPlugin):
    """Base class for storage providers."""

    def put(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Store an object."""
        raise NotImplementedError

    def get(self, key: str, default: Any = None, **kwargs: Any) -> Any:
        """Retrieve an object."""
        raise NotImplementedError

    def delete(self, key: str, **kwargs: Any) -> None:
        """Delete an object."""
        raise NotImplementedError

    def list_keys(self, pattern: Optional[str] = None, **kwargs: Any) -> List[str]:
        """List object keys."""
        raise NotImplementedError

    def get_metadata(self, key: str, **kwargs: Any) -> Dict[str, Any]:
        """Get object metadata."""
        raise NotImplementedError

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities."""
        raise NotImplementedError


class ObjectStoreProvider(StorageProvider):
    """Object Store persistence provider.

    This provider handles data persistence using S3-compatible object storage services.
    Supports AWS S3, MinIO, and other S3-compatible services.
    """

    name = "object_store"
    version = "0.1.0"
    description = "Object Store persistence provider for S3-compatible services"
    author = "PepperPy Team"

    # Attributes auto-bound from plugin.yaml with default fallback values
    api_key: str = ""
    client: Optional[httpx.AsyncClient] = None
    bucket_name: str = "pepperpy"
    endpoint_url: Optional[str] = None
    region_name: str = "us-east-1"
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session: Optional[aioboto3.Session] = None
    logger = get_logger(__name__)

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        if self.initialized:
            return

        # Create S3 session
        self.session = aioboto3.Session(
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name,
        )

        # Create HTTP client for direct operations
        base_url = (
            str(httpx.URL(urljoin("https://", self.endpoint_url)))
            if self.endpoint_url
            else ""
        )
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

        self.initialized = True
        self.logger.debug(
            f"Initialized with bucket={self.bucket_name}, endpoint={self.endpoint_url}"
        )

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        """
        if self.client:
            await self.client.aclose()
            self.client = None

        self.session = None
        self.initialized = False
        self.logger.debug("Resources cleaned up")

    async def validate(self) -> None:
        """Validate the provider configuration.

        Raises:
            PersistenceError: If the configuration is invalid
        """
        if self.bucket_name and not isinstance(self.bucket_name, str):
            raise PersistenceError("Bucket name must be a string")

        # AWS credentials can be None if using IAM roles or environment variables
        if self.access_key_id and not self.secret_access_key:
            raise PersistenceError(
                "AWS secret access key is required when providing access key ID"
            )

        if self.secret_access_key and not self.access_key_id:
            raise PersistenceError(
                "AWS access key ID is required when providing secret access key"
            )

    async def list_buckets(self) -> List[str]:
        """List all buckets.

        Returns:
            List of bucket names.

        Raises:
            PersistenceError: If listing fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            async with self.client as client:
                response = await client.get("/")
                return [bucket["Name"] for bucket in response.json().get("Buckets", [])]

        except Exception as e:
            raise PersistenceError(f"Error listing buckets: {e!s}") from e

    async def create_bucket(self, name: str) -> None:
        """Create a bucket.

        Args:
            name: Bucket name.

        Raises:
            PersistenceError: If creation fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            # Check if bucket exists
            try:
                async with self.client as client:
                    response = await client.get(f"/{name}")
                    response.raise_for_status()
                    return  # Bucket already exists
            except Exception:
                # Bucket doesn't exist, create it
                async with self.client as client:
                    # For AWS S3, use LocationConstraint
                    if self.region_name and self.endpoint_url is None:
                        await client.put(
                            f"/{name}", json={"LocationConstraint": self.region_name}
                        )
                    else:
                        # For non-AWS implementations
                        await client.put(f"/{name}")

        except Exception as e:
            raise PersistenceError(f"Error creating bucket: {e!s}") from e

    async def delete_bucket(self, name: str, force: bool = False) -> None:
        """Delete a bucket.

        Args:
            name: Bucket name.
            force: Whether to delete all objects in the bucket first.

        Raises:
            PersistenceError: If deletion fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            # Delete all objects if force is True
            if force:
                await self.delete_all_objects(name)

            # Delete bucket
            async with self.client as client:
                await client.delete(f"/{name}")

        except Exception as e:
            raise PersistenceError(f"Error deleting bucket: {e!s}") from e

    async def list_objects(
        self,
        bucket: Optional[str] = None,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> List[Dict[str, Any]]:
        """List objects in a bucket.

        Args:
            bucket: Bucket name (defaults to default_bucket).
            prefix: Object prefix to filter by.
            max_keys: Maximum number of keys to return.

        Returns:
            List of object information.

        Raises:
            PersistenceError: If listing fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.bucket_name
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # List objects
            async with self.client as client:
                response = await client.get(
                    f"/{bucket_name}?list=true&prefix={prefix}&max-keys={max_keys}"
                )
                response.raise_for_status()
                objects = response.json().get("Contents", [])

                return [
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                        "etag": obj["ETag"],
                        "storage_class": obj.get("StorageClass", ""),
                    }
                    for obj in objects
                ]

        except Exception as e:
            raise PersistenceError(f"Error listing objects: {e!s}") from e

    async def upload_object(
        self,
        key: str,
        data: Union[bytes, str, BytesIO, Path],
        bucket: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Upload an object to a bucket.

        Args:
            key: Object key.
            data: Object data (bytes, string, file-like object, or path).
            bucket: Bucket name (defaults to default_bucket).
            content_type: Content type of the object.
            metadata: Optional metadata to associate with the object.

        Returns:
            Upload result information.

        Raises:
            PersistenceError: If upload fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.bucket_name
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Prepare data
            if isinstance(data, str):
                if os.path.isfile(data):
                    # Load from file path
                    with open(data, "rb") as f:
                        body = f.read()
                else:
                    # Treat as string content
                    body = data.encode("utf-8")
            elif isinstance(data, Path):
                # Load from Path
                with open(data, "rb") as f:
                    body = f.read()
            elif isinstance(data, BytesIO):
                # Get bytes from BytesIO
                body = data.getvalue()
            else:
                # Use as is (bytes)
                body = data

            # Prepare upload parameters
            upload_params = {
                "Bucket": bucket_name,
                "Key": key,
                "Body": body,
            }

            # Add content type if provided
            if content_type:
                upload_params["ContentType"] = content_type

            # Add metadata if provided
            if metadata:
                upload_params["Metadata"] = metadata

            # Upload object
            async with self.client as client:
                response = await client.put(f"/{bucket_name}/{key}", json=upload_params)
                response.raise_for_status()

                # Calculate MD5 for verification
                if isinstance(body, bytes):
                    md5 = hashlib.md5(body).digest()
                else:
                    # Convert to bytes if not already
                    body_bytes = (
                        body if isinstance(body, bytes) else str(body).encode("utf-8")
                    )
                    md5 = hashlib.md5(body_bytes).digest()

                calculated_etag = f'"{base64.b64encode(md5).decode("utf-8")}"'

                return {
                    "key": key,
                    "etag": response.headers.get("ETag", ""),
                    "calculated_etag": calculated_etag,
                    "content_type": content_type,
                    "size": len(body) if hasattr(body, "__len__") else 0,
                }

        except Exception as e:
            raise PersistenceError(f"Error uploading object: {e!s}") from e

    async def download_object(
        self,
        key: str,
        bucket: Optional[str] = None,
        version_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Download an object from a bucket.

        Args:
            key: Object key.
            bucket: Bucket name (defaults to default_bucket).
            version_id: Optional version ID for versioned objects.

        Returns:
            Object data and metadata.

        Raises:
            PersistenceError: If download fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.bucket_name
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Prepare download parameters
            download_params = {
                "Bucket": bucket_name,
                "Key": key,
            }

            # Add version ID if provided
            if version_id:
                download_params["VersionId"] = version_id

            # Download object
            async with self.client as client:
                response = await client.get(
                    f"/{bucket_name}/{key}", params=download_params
                )
                response.raise_for_status()

                # Read body
                body = await response.read()

                return {
                    "key": key,
                    "data": body,
                    "content_type": response.headers.get("Content-Type", ""),
                    "content_length": response.headers.get("Content-Length", 0),
                    "last_modified": response.headers.get("Last-Modified"),
                    "etag": response.headers.get("ETag", ""),
                    "metadata": response.headers.get("Metadata", {}),
                    "version_id": response.headers.get("VersionId"),
                }

        except Exception as e:
            raise PersistenceError(f"Error downloading object: {e!s}") from e

    async def delete_object(
        self,
        key: str,
        bucket: Optional[str] = None,
        version_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete an object from a bucket.

        Args:
            key: Object key.
            bucket: Bucket name (defaults to default_bucket).
            version_id: Optional version ID for versioned objects.

        Returns:
            Deletion result information.

        Raises:
            PersistenceError: If deletion fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.bucket_name
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Prepare deletion parameters
            delete_params = {
                "Bucket": bucket_name,
                "Key": key,
            }

            # Add version ID if provided
            if version_id:
                delete_params["VersionId"] = version_id

            # Delete object
            async with self.client as client:
                response = await client.delete(
                    f"/{bucket_name}/{key}", params=delete_params
                )
                response.raise_for_status()

                return {
                    "key": key,
                    "version_id": response.headers.get("VersionId"),
                    "delete_marker": response.headers.get("Delete-Marker", False),
                }

        except Exception as e:
            raise PersistenceError(f"Error deleting object: {e!s}") from e

    async def delete_objects(
        self,
        keys: List[str],
        bucket: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete multiple objects from a bucket.

        Args:
            keys: List of object keys to delete.
            bucket: Bucket name (defaults to default_bucket).

        Returns:
            Deletion result information.

        Raises:
            PersistenceError: If deletion fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.bucket_name
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Prepare objects to delete
            objects = [{"Key": key} for key in keys]

            # Delete objects
            async with self.client as client:
                response = await client.post(
                    f"/{bucket_name}?delete=true", json={"Objects": objects}
                )
                response.raise_for_status()

                return {
                    "deleted": [
                        obj.get("Key") for obj in response.json().get("Deleted", [])
                    ],
                    "errors": [
                        {
                            "key": err.get("Key"),
                            "code": err.get("Code"),
                            "message": err.get("Message"),
                        }
                        for err in response.json().get("Errors", [])
                    ],
                }

        except Exception as e:
            raise PersistenceError(f"Error deleting objects: {e!s}") from e

    async def delete_all_objects(self, bucket: Optional[str] = None) -> Dict[str, Any]:
        """Delete all objects from a bucket.

        Args:
            bucket: Bucket name (defaults to default_bucket).

        Returns:
            Deletion result information.

        Raises:
            PersistenceError: If deletion fails.
        """
        try:
            bucket_name = bucket or self.bucket_name
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # List all objects
            objects = await self.list_objects(bucket=bucket_name)
            keys = [obj["key"] for obj in objects]

            # Delete objects in batches of 1000 (S3 limit)
            results = {
                "deleted": [],
                "errors": [],
            }

            for i in range(0, len(keys), 1000):
                batch = keys[i : i + 1000]
                if batch:
                    result = await self.delete_objects(batch, bucket=bucket_name)
                    results["deleted"].extend(result["deleted"])
                    results["errors"].extend(result["errors"])

            return results

        except Exception as e:
            raise PersistenceError(f"Error deleting all objects: {e!s}") from e

    async def copy_object(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: Optional[str] = None,
        dest_bucket: Optional[str] = None,
        source_version_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Copy an object from one location to another.

        Args:
            source_key: Source object key.
            dest_key: Destination object key.
            source_bucket: Source bucket name (defaults to default_bucket).
            dest_bucket: Destination bucket name (defaults to default_bucket).
            source_version_id: Optional version ID for versioned source object.

        Returns:
            Copy result information.

        Raises:
            PersistenceError: If copy fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            source_bucket_name = source_bucket or self.bucket_name
            dest_bucket_name = dest_bucket or self.bucket_name
            if not source_bucket_name or not dest_bucket_name:
                raise PersistenceError("No bucket specified")

            # Prepare copy source
            copy_source = {
                "Bucket": source_bucket_name,
                "Key": source_key,
            }

            # Add version ID if provided
            if source_version_id:
                copy_source["VersionId"] = source_version_id

            # Copy object
            async with self.client as client:
                response = await client.post(
                    f"/{dest_bucket_name}/{dest_key}?copy=true",
                    json={"CopySource": copy_source},
                )
                response.raise_for_status()

                return {
                    "source_key": source_key,
                    "dest_key": dest_key,
                    "etag": response.headers.get("ETag", ""),
                    "last_modified": response.headers.get("Last-Modified"),
                    "version_id": response.headers.get("VersionId"),
                }

        except Exception as e:
            raise PersistenceError(f"Error copying object: {e!s}") from e

    async def generate_presigned_url(
        self,
        key: str,
        method: str = "GET",
        expires_in: int = 3600,
        bucket: Optional[str] = None,
    ) -> str:
        """Generate a pre-signed URL for object access.

        Args:
            key: Object key
            method: HTTP method (GET, PUT, etc.)
            expires_in: URL expiration time in seconds
            bucket: Optional bucket name

        Returns:
            Pre-signed URL as string

        Raises:
            PersistenceError: If URL generation fails
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.bucket_name
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Generate URL
            async with self.client as client:
                response = await client.get(
                    f"/{bucket_name}/{key}",
                    params={
                        "presigned": "true",
                        "expires-in": str(expires_in),
                        "method": method.upper(),
                    },
                )
                response.raise_for_status()
                return response.text

        except Exception as e:
            raise PersistenceError(f"Error generating pre-signed URL: {e!s}") from e

    async def get_object_metadata(
        self,
        key: str,
        bucket: Optional[str] = None,
        version_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get metadata for an object.

        Args:
            key: Object key.
            bucket: Bucket name (defaults to default_bucket).
            version_id: Optional version ID for versioned objects.

        Returns:
            Object metadata.

        Raises:
            PersistenceError: If metadata retrieval fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.bucket_name
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Prepare parameters
            params = {
                "Bucket": bucket_name,
                "Key": key,
            }

            # Add version ID if provided
            if version_id:
                params["VersionId"] = version_id

            # Get metadata
            async with self.client as client:
                response = await client.head(f"/{bucket_name}/{key}", params=params)
                response.raise_for_status()

                return {
                    "key": key,
                    "content_type": response.headers.get("Content-Type", ""),
                    "content_length": response.headers.get("Content-Length", 0),
                    "last_modified": response.headers.get("Last-Modified"),
                    "etag": response.headers.get("ETag", ""),
                    "metadata": response.headers.get("Metadata", {}),
                    "version_id": response.headers.get("VersionId"),
                    "storage_class": response.headers.get("StorageClass", ""),
                }

        except Exception as e:
            raise PersistenceError(f"Error getting object metadata: {e!s}") from e


class ObjectStore:
    """High-level interface for object storage.

    This class provides a simplified interface for storing and retrieving
    objects using a storage provider. It handles serialization,
    validation, and error handling.

    Args:
        provider: Storage provider instance
        namespace: Optional namespace for keys
        **kwargs: Additional store options

    Example:
        >>> store = ObjectStore(provider, namespace="app1")
        >>> store.put("settings", {"theme": "dark"})
        >>> settings = store.get("settings")
        >>> assert settings["theme"] == "dark"
    """

    def __init__(
        self,
        provider: StorageProvider,
        namespace: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the object store.

        Args:
            provider: Storage provider instance
            namespace: Optional namespace for keys
            **kwargs: Additional store options

        Raises:
            ValidationError: If provider is invalid
        """
        if not isinstance(provider, StorageProvider):
            raise ValidationError("Invalid storage provider")

        self.provider = provider
        self.namespace = namespace
        self.options = kwargs

    def _make_key(self, key: str) -> str:
        """Create a namespaced key.

        Args:
            key: Original key

        Returns:
            Namespaced key
        """
        if self.namespace:
            return f"{self.namespace}:{key}"
        return key

    def put(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Store an object.

        Args:
            key: Object key
            value: Object to store
            metadata: Optional object metadata
            **kwargs: Additional storage options
                - ttl: Time-to-live in seconds
                - encoding: Content encoding
                - version: Version identifier

        Raises:
            StorageError: If storage fails
            ValidationError: If key or value is invalid

        Example:
            >>> store.put(
            ...     "user:123",
            ...     {"name": "Alice", "active": True},
            ...     metadata={"type": "user"},
            ...     ttl=3600
            ... )
        """
        if not key:
            raise ValidationError("Key cannot be empty")

        try:
            namespaced_key = self._make_key(key)
            self.provider.put(
                namespaced_key,
                value,
                metadata=metadata,
                **{**self.options, **kwargs},
            )
        except Exception as e:
            raise StorageError(f"Failed to store object: {e}")

    def get(
        self,
        key: str,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Retrieve an object.

        Args:
            key: Object key
            default: Default value if not found
            **kwargs: Additional retrieval options
                - version: Specific version
                - encoding: Content encoding

        Returns:
            The stored object or default value

        Raises:
            StorageError: If retrieval fails
            ValidationError: If key is invalid

        Example:
            >>> data = store.get(
            ...     "user:123",
            ...     default={},
            ...     version="latest"
            ... )
            >>> print(data.get("name"))
        """
        if not key:
            raise ValidationError("Key cannot be empty")

        try:
            namespaced_key = self._make_key(key)
            return self.provider.get(
                namespaced_key,
                default=default,
                **{**self.options, **kwargs},
            )
        except Exception as e:
            if default is not None:
                return default
            raise StorageError(f"Failed to retrieve object: {e}")

    def delete(self, key: str, **kwargs: Any) -> None:
        """Delete an object.

        Args:
            key: Object key
            **kwargs: Additional deletion options
                - force: Force deletion
                - version: Specific version

        Raises:
            StorageError: If deletion fails
            ValidationError: If key is invalid

        Example:
            >>> store.delete("user:123", force=True)
        """
        if not key:
            raise ValidationError("Key cannot be empty")

        try:
            namespaced_key = self._make_key(key)
            self.provider.delete(
                namespaced_key,
                **{**self.options, **kwargs},
            )
        except Exception as e:
            raise StorageError(f"Failed to delete object: {e}")

    def list_keys(
        self,
        pattern: Optional[str] = None,
        **kwargs: Any,
    ) -> List[str]:
        """List object keys.

        Args:
            pattern: Optional pattern to filter keys
            **kwargs: Additional listing options
                - prefix: Key prefix
                - limit: Maximum keys
                - offset: Starting offset

        Returns:
            List of matching keys

        Example:
            >>> keys = store.list_keys("user:*", limit=10)
            >>> for key in keys:
            ...     print(key)
        """
        try:
            if pattern and self.namespace:
                pattern = self._make_key(pattern)

            keys = self.provider.list_keys(
                pattern=pattern,
                **{**self.options, **kwargs},
            )

            # Remove namespace prefix if present
            if self.namespace:
                prefix = f"{self.namespace}:"
                keys = [key[len(prefix) :] for key in keys if key.startswith(prefix)]

            return keys
        except Exception as e:
            raise StorageError(f"Failed to list keys: {e}")

    def get_metadata(self, key: str, **kwargs: Any) -> Dict[str, Any]:
        """Get object metadata.

        Args:
            key: Object key
            **kwargs: Additional metadata options

        Returns:
            Object metadata

        Raises:
            StorageError: If metadata retrieval fails
            ValidationError: If key is invalid

        Example:
            >>> metadata = store.get_metadata("user:123")
            >>> print(metadata.get("created_at"))
        """
        if not key:
            raise ValidationError("Key cannot be empty")

        try:
            namespaced_key = self._make_key(key)
            return self.provider.get_metadata(
                namespaced_key,
                **{**self.options, **kwargs},
            )
        except Exception as e:
            raise StorageError(f"Failed to get metadata: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get store capabilities.

        Returns:
            Dict with store capabilities including:
                - provider: Provider type
                - namespace: Store namespace
                - supports_ttl: TTL support
                - supports_versioning: Version control
                - supports_metadata: Metadata support
                - max_value_size: Size limits
                - supported_patterns: Key patterns

        Example:
            >>> caps = store.get_capabilities()
            >>> if caps["supports_ttl"]:
            ...     store.put("temp", "value", ttl=60)
        """
        capabilities = self.provider.get_capabilities()
        capabilities.update({
            "namespace": self.namespace,
            "options": self.options,
        })
        return capabilities
