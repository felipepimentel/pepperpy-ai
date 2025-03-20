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

import aioboto3

from pepperpy.core.errors import ProviderError
from pepperpy.core.validation import ValidationError
from pepperpy.providers.base import BaseProvider

from .provider import StorageError, StorageProvider


class PersistenceError(ProviderError):
    """Exception raised for persistence-related errors."""

    pass


class ObjectStoreProvider(BaseProvider):
    """Object Store persistence provider.

    This provider handles data persistence using S3-compatible object storage services.
    Supports AWS S3, MinIO, and other S3-compatible services.
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        default_bucket: Optional[str] = None,
        create_buckets: bool = False,
        provider_name: str = "object_store",
        provider_type: str = "data",
        **kwargs: Any,
    ) -> None:
        """Initialize the S3 client.

        Args:
            endpoint_url: Custom endpoint URL for the S3 service
            region_name: AWS region name
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            default_bucket: Default bucket to use if none specified
            create_buckets: Whether to create buckets if they don't exist
            provider_name: Name of the provider
            provider_type: Type of the provider
            **kwargs: Additional arguments to pass to the S3 client
        """
        super().__init__(provider_name=provider_name, provider_type=provider_type)

        # Add object storage capabilities
        self.add_capability("object_store")
        self.add_capability("file_storage")
        self.add_capability("blob_storage")

        # Store configuration
        self.endpoint_url = endpoint_url
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.default_bucket = default_bucket
        self.create_buckets = create_buckets
        self.client_kwargs = kwargs

        # Initialize session and client to None
        self.session = None
        self.client = None
        self.resource = None

    async def validate(self) -> None:
        """Validate the provider configuration.

        Raises:
            PersistenceError: If the configuration is invalid
        """
        if self.default_bucket and not isinstance(self.default_bucket, str):
            raise PersistenceError("Default bucket must be a string")

        # AWS credentials can be None if using IAM roles or environment variables
        if self.aws_access_key_id and not self.aws_secret_access_key:
            raise PersistenceError(
                "AWS secret access key is required when providing access key ID"
            )

        if self.aws_secret_access_key and not self.aws_access_key_id:
            raise PersistenceError(
                "AWS access key ID is required when providing secret access key"
            )

    async def initialize(self) -> None:
        """Initialize the provider.

        This method connects to the object storage service.

        Raises:
            PersistenceError: If initialization fails
        """
        await self.connect()

    async def close(self) -> None:
        """Close the provider.

        This method disconnects from the object storage service.

        Raises:
            PersistenceError: If cleanup fails
        """
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to the object store.

        Raises:
            PersistenceError: If connection fails.
        """
        try:
            # Create session
            self.session = aioboto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            )

            # Create client
            self.client = self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                **self.client_kwargs,
            )

            # Create resource
            self.resource = self.session.resource(
                "s3",
                endpoint_url=self.endpoint_url,
                **self.client_kwargs,
            )

            # Create default bucket if needed
            if self.default_bucket and self.create_buckets:
                await self.create_bucket(self.default_bucket)

        except Exception as e:
            raise PersistenceError(f"Error connecting to object store: {str(e)}") from e

    async def disconnect(self) -> None:
        """Disconnect from the object store.

        Raises:
            PersistenceError: If disconnection fails.
        """
        try:
            if self.client:
                await self.client.__aexit__(None, None, None)
                self.client = None

            if self.resource:
                await self.resource.__aexit__(None, None, None)
                self.resource = None

            self.session = None

        except Exception as e:
            raise PersistenceError(
                f"Error disconnecting from object store: {str(e)}"
            ) from e

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
                response = await client.list_buckets()
                return [bucket["Name"] for bucket in response.get("Buckets", [])]

        except Exception as e:
            raise PersistenceError(f"Error listing buckets: {str(e)}") from e

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
                    await client.head_bucket(Bucket=name)
                    return  # Bucket already exists
            except Exception:
                # Bucket doesn't exist, create it
                async with self.client as client:
                    # For AWS S3, use LocationConstraint
                    if self.region_name and self.endpoint_url is None:
                        await client.create_bucket(
                            Bucket=name,
                            CreateBucketConfiguration={
                                "LocationConstraint": self.region_name,
                            },
                        )
                    else:
                        # For non-AWS implementations
                        await client.create_bucket(Bucket=name)

        except Exception as e:
            raise PersistenceError(f"Error creating bucket: {str(e)}") from e

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
                await client.delete_bucket(Bucket=name)

        except Exception as e:
            raise PersistenceError(f"Error deleting bucket: {str(e)}") from e

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

            bucket_name = bucket or self.default_bucket
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # List objects
            async with self.client as client:
                paginator = client.get_paginator("list_objects_v2")
                objects = []

                async for page in paginator.paginate(
                    Bucket=bucket_name,
                    Prefix=prefix,
                    MaxKeys=max_keys,
                ):
                    if "Contents" in page:
                        for obj in page["Contents"]:
                            objects.append({
                                "key": obj.get("Key", ""),
                                "size": obj.get("Size", 0),
                                "last_modified": obj.get("LastModified"),
                                "etag": obj.get("ETag", "").strip('"'),
                                "storage_class": obj.get("StorageClass", ""),
                            })

                return objects

        except Exception as e:
            raise PersistenceError(f"Error listing objects: {str(e)}") from e

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

            bucket_name = bucket or self.default_bucket
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
                response = await client.put_object(**upload_params)

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
                    "etag": response.get("ETag", ""),
                    "calculated_etag": calculated_etag,
                    "content_type": content_type,
                    "size": len(body) if hasattr(body, "__len__") else 0,
                }

        except Exception as e:
            raise PersistenceError(f"Error uploading object: {str(e)}") from e

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

            bucket_name = bucket or self.default_bucket
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
                response = await client.get_object(**download_params)

                # Read body
                body = await response["Body"].read()
                await response["Body"].close()

                return {
                    "key": key,
                    "data": body,
                    "content_type": response.get("ContentType", ""),
                    "content_length": response.get("ContentLength", 0),
                    "last_modified": response.get("LastModified"),
                    "etag": response.get("ETag", "").strip('"'),
                    "metadata": response.get("Metadata", {}),
                    "version_id": response.get("VersionId"),
                }

        except Exception as e:
            raise PersistenceError(f"Error downloading object: {str(e)}") from e

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

            bucket_name = bucket or self.default_bucket
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
                response = await client.delete_object(**delete_params)

                return {
                    "key": key,
                    "version_id": response.get("VersionId"),
                    "delete_marker": response.get("DeleteMarker", False),
                }

        except Exception as e:
            raise PersistenceError(f"Error deleting object: {str(e)}") from e

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

            bucket_name = bucket or self.default_bucket
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Prepare objects to delete
            objects = [{"Key": key} for key in keys]

            # Delete objects
            async with self.client as client:
                response = await client.delete_objects(
                    Bucket=bucket_name,
                    Delete={
                        "Objects": objects,
                        "Quiet": False,
                    },
                )

                return {
                    "deleted": [obj.get("Key") for obj in response.get("Deleted", [])],
                    "errors": [
                        {
                            "key": err.get("Key"),
                            "code": err.get("Code"),
                            "message": err.get("Message"),
                        }
                        for err in response.get("Errors", [])
                    ],
                }

        except Exception as e:
            raise PersistenceError(f"Error deleting objects: {str(e)}") from e

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
            bucket_name = bucket or self.default_bucket
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
            raise PersistenceError(f"Error deleting all objects: {str(e)}") from e

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

            source_bucket_name = source_bucket or self.default_bucket
            dest_bucket_name = dest_bucket or self.default_bucket
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
                response = await client.copy_object(
                    CopySource=copy_source,
                    Bucket=dest_bucket_name,
                    Key=dest_key,
                )

                return {
                    "source_key": source_key,
                    "dest_key": dest_key,
                    "etag": response.get("CopyObjectResult", {})
                    .get("ETag", "")
                    .strip('"'),
                    "last_modified": response.get("CopyObjectResult", {}).get(
                        "LastModified"
                    ),
                    "version_id": response.get("VersionId"),
                }

        except Exception as e:
            raise PersistenceError(f"Error copying object: {str(e)}") from e

    async def generate_presigned_url(
        self,
        key: str,
        bucket: Optional[str] = None,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> str:
        """Generate a presigned URL for an object.

        Args:
            key: Object key.
            bucket: Bucket name (defaults to default_bucket).
            expires_in: URL expiration time in seconds.
            method: HTTP method ("GET", "PUT", etc).

        Returns:
            Presigned URL.

        Raises:
            PersistenceError: If URL generation fails.
        """
        try:
            if not self.client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.default_bucket
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Generate URL
            async with self.client as client:
                url = await client.generate_presigned_url(
                    ClientMethod=f"{method.lower()}_object",
                    Params={
                        "Bucket": bucket_name,
                        "Key": key,
                    },
                    ExpiresIn=expires_in,
                )

                return url

        except Exception as e:
            raise PersistenceError(f"Error generating presigned URL: {str(e)}") from e

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

            bucket_name = bucket or self.default_bucket
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
                response = await client.head_object(**params)

                return {
                    "key": key,
                    "content_type": response.get("ContentType", ""),
                    "content_length": response.get("ContentLength", 0),
                    "last_modified": response.get("LastModified"),
                    "etag": response.get("ETag", "").strip('"'),
                    "metadata": response.get("Metadata", {}),
                    "version_id": response.get("VersionId"),
                    "storage_class": response.get("StorageClass", ""),
                }

        except Exception as e:
            raise PersistenceError(f"Error getting object metadata: {str(e)}") from e


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
