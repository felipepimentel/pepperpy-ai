"""Object Store persistence provider implementation.

This module provides functionality for data persistence using object storage services.
"""

import base64
import hashlib
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aioboto3


class ObjectStoreProvider:
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
        **kwargs: Any,
    ) -> None:
        """Initialize the Object Store provider.

        Args:
            endpoint_url: Endpoint URL for the S3 service (required for non-AWS implementations).
            region_name: AWS region name.
            aws_access_key_id: AWS access key ID.
            aws_secret_access_key: AWS secret access key.
            default_bucket: Default bucket to use for operations.
            create_buckets: Whether to create buckets if they don't exist.
            **kwargs: Additional keyword arguments passed to the S3 client.
        """
        self.endpoint_url = endpoint_url
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.default_bucket = default_bucket
        self.create_buckets = create_buckets
        self.client_kwargs = kwargs

        # Initialize session and client
        self._session: Optional[aioboto3.Session] = None
        self._client: Optional[Any] = None
        self._resource: Optional[Any] = None

    async def connect(self) -> None:
        """Connect to the object store.

        Raises:
            PersistenceError: If connection fails.
        """
        try:
            # Create session
            self._session = aioboto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            )

            # Create client
            self._client = self._session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                **self.client_kwargs,
            )

            # Create resource
            self._resource = self._session.resource(
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
            if self._client:
                await self._client.__aexit__(None, None, None)
                self._client = None

            if self._resource:
                await self._resource.__aexit__(None, None, None)
                self._resource = None

            self._session = None

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
            if not self._client:
                raise PersistenceError("Not connected to object store")

            async with self._client as client:
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
            if not self._client:
                raise PersistenceError("Not connected to object store")

            # Check if bucket exists
            try:
                async with self._client as client:
                    await client.head_bucket(Bucket=name)
                    return  # Bucket already exists
            except Exception:
                # Bucket doesn't exist, create it
                async with self._client as client:
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
            if not self._client:
                raise PersistenceError("Not connected to object store")

            # Delete all objects if force is True
            if force:
                await self.delete_all_objects(name)

            # Delete bucket
            async with self._client as client:
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
            if not self._client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.default_bucket
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # List objects
            async with self._client as client:
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
            if not self._client:
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
            async with self._client as client:
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
            if not self._client:
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
            async with self._client as client:
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
            if not self._client:
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
            async with self._client as client:
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
            if not self._client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.default_bucket
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Prepare objects to delete
            objects = [{"Key": key} for key in keys]

            # Delete objects
            async with self._client as client:
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
            if not self._client:
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
            async with self._client as client:
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
            if not self._client:
                raise PersistenceError("Not connected to object store")

            bucket_name = bucket or self.default_bucket
            if not bucket_name:
                raise PersistenceError("No bucket specified")

            # Generate URL
            async with self._client as client:
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
            if not self._client:
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
            async with self._client as client:
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
