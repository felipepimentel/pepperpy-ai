"""AWS provider for the Pepperpy framework.

This module provides AWS integration including:
- S3 storage
- DynamoDB tables
- SQS queues
- Lambda functions
- CloudWatch monitoring
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

import aioboto3
from botocore.exceptions import BotoCoreError, ClientError

from pepperpy.core.errors import ProviderError, ValidationError
from pepperpy.core.types import ComponentState
from pepperpy.providers.base import BaseProvider


class AWSProvider(BaseProvider):
    """AWS service provider."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize AWS provider.

        Args:
            config: AWS configuration
        """
        super().__init__(name="aws")
        self._config = config
        self._session = None
        self._state = ComponentState.CREATED
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize AWS provider.

        Raises:
            ProviderError: If initialization fails
        """
        try:
            self._state = ComponentState.INITIALIZING
            self._session = aioboto3.Session(
                region_name=self._config["credentials"]["region"],
                profile_name=self._config["credentials"].get("profile"),
                aws_access_key_id=self._config["credentials"].get("access_key_id"),
                aws_secret_access_key=self._config["credentials"].get("secret_access_key"),
            )
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ProviderError(f"Failed to initialize AWS provider: {e}")

    async def cleanup(self) -> None:
        """Clean up AWS provider.

        Raises:
            ProviderError: If cleanup fails
        """
        try:
            self._state = ComponentState.CLEANING
            if self._session:
                # Close any open connections
                pass
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ProviderError(f"Failed to clean up AWS provider: {e}")

    async def validate_config(self) -> bool:
        """Validate AWS configuration.

        Returns:
            bool: True if configuration is valid

        Raises:
            ValidationError: If configuration is invalid
        """
        required_fields = ["credentials", "services"]
        if not all(field in self._config for field in required_fields):
            raise ValidationError(
                f"Missing required fields in AWS config: {required_fields}"
            )
        return True

    async def list_buckets(self) -> list[str]:
        """List S3 buckets.

        Returns:
            list[str]: List of bucket names

        Raises:
            ProviderError: If operation fails
        """
        try:
            async with self._session.client("s3") as s3:
                response = await s3.list_buckets()
                return [bucket["Name"] for bucket in response["Buckets"]]
        except (BotoCoreError, ClientError) as e:
            raise ProviderError(f"Failed to list S3 buckets: {e}")

    async def upload_file(
        self,
        bucket: str,
        key: str,
        data: bytes | AsyncIterator[bytes],
    ) -> None:
        """Upload file to S3.

        Args:
            bucket: Bucket name
            key: Object key
            data: File data

        Raises:
            ProviderError: If upload fails
        """
        try:
            async with self._session.client("s3") as s3:
                if isinstance(data, bytes):
                    await s3.put_object(Bucket=bucket, Key=key, Body=data)
                else:
                    # Handle streaming upload
                    multipart = await s3.create_multipart_upload(
                        Bucket=bucket,
                        Key=key,
                    )
                    try:
                        parts = []
                        part_number = 1
                        async for chunk in data:
                            part = await s3.upload_part(
                                Bucket=bucket,
                                Key=key,
                                PartNumber=part_number,
                                UploadId=multipart["UploadId"],
                                Body=chunk,
                            )
                            parts.append({
                                "PartNumber": part_number,
                                "ETag": part["ETag"],
                            })
                            part_number += 1
                        await s3.complete_multipart_upload(
                            Bucket=bucket,
                            Key=key,
                            UploadId=multipart["UploadId"],
                            MultipartUpload={"Parts": parts},
                        )
                    except Exception as e:
                        await s3.abort_multipart_upload(
                            Bucket=bucket,
                            Key=key,
                            UploadId=multipart["UploadId"],
                        )
                        raise ProviderError(f"Failed to upload file: {e}")
        except (BotoCoreError, ClientError) as e:
            raise ProviderError(f"Failed to upload file: {e}")

    async def download_file(
        self,
        bucket: str,
        key: str,
    ) -> AsyncIterator[bytes]:
        """Download file from S3.

        Args:
            bucket: Bucket name
            key: Object key

        Yields:
            bytes: File data chunks

        Raises:
            ProviderError: If download fails
        """
        try:
            async with self._session.client("s3") as s3:
                response = await s3.get_object(Bucket=bucket, Key=key)
                async with response["Body"] as stream:
                    while True:
                        chunk = await stream.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        yield chunk
        except (BotoCoreError, ClientError) as e:
            raise ProviderError(f"Failed to download file: {e}")

    async def delete_file(self, bucket: str, key: str) -> None:
        """Delete file from S3.

        Args:
            bucket: Bucket name
            key: Object key

        Raises:
            ProviderError: If deletion fails
        """
        try:
            async with self._session.client("s3") as s3:
                await s3.delete_object(Bucket=bucket, Key=key)
        except (BotoCoreError, ClientError) as e:
            raise ProviderError(f"Failed to delete file: {e}")

    async def send_message(
        self,
        queue_url: str,
        message: str,
        delay_seconds: int = 0,
    ) -> None:
        """Send message to SQS queue.

        Args:
            queue_url: Queue URL
            message: Message body
            delay_seconds: Message delay in seconds

        Raises:
            ProviderError: If send fails
        """
        try:
            async with self._session.client("sqs") as sqs:
                await sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=message,
                    DelaySeconds=delay_seconds,
                )
        except (BotoCoreError, ClientError) as e:
            raise ProviderError(f"Failed to send message: {e}")

    async def receive_messages(
        self,
        queue_url: str,
        max_messages: int = 10,
        wait_time: int = 20,
    ) -> list[dict[str, Any]]:
        """Receive messages from SQS queue.

        Args:
            queue_url: Queue URL
            max_messages: Maximum number of messages to receive
            wait_time: Long polling wait time in seconds

        Returns:
            list[dict]: List of messages

        Raises:
            ProviderError: If receive fails
        """
        try:
            async with self._session.client("sqs") as sqs:
                response = await sqs.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=max_messages,
                    WaitTimeSeconds=wait_time,
                )
                return response.get("Messages", [])
        except (BotoCoreError, ClientError) as e:
            raise ProviderError(f"Failed to receive messages: {e}")

    async def delete_message(self, queue_url: str, receipt_handle: str) -> None:
        """Delete message from SQS queue.

        Args:
            queue_url: Queue URL
            receipt_handle: Message receipt handle

        Raises:
            ProviderError: If deletion fails
        """
        try:
            async with self._session.client("sqs") as sqs:
                await sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle,
                )
        except (BotoCoreError, ClientError) as e:
            raise ProviderError(f"Failed to delete message: {e}")

    async def invoke_lambda(
        self,
        function_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Invoke Lambda function.

        Args:
            function_name: Function name or ARN
            payload: Function payload

        Returns:
            dict: Function response

        Raises:
            ProviderError: If invocation fails
        """
        try:
            async with self._session.client("lambda") as lambda_client:
                response = await lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType="RequestResponse",
                    Payload=payload,
                )
                return response["Payload"]
        except (BotoCoreError, ClientError) as e:
            raise ProviderError(f"Failed to invoke Lambda function: {e}")

    async def put_metric(
        self,
        namespace: str,
        name: str,
        value: float,
        unit: str,
        dimensions: list[dict[str, str]] | None = None,
    ) -> None:
        """Put metric to CloudWatch.

        Args:
            namespace: Metric namespace
            name: Metric name
            value: Metric value
            unit: Metric unit
            dimensions: Optional metric dimensions

        Raises:
            ProviderError: If operation fails
        """
        try:
            async with self._session.client("cloudwatch") as cloudwatch:
                await cloudwatch.put_metric_data(
                    Namespace=namespace,
                    MetricData=[{
                        "MetricName": name,
                        "Value": value,
                        "Unit": unit,
                        "Dimensions": dimensions or [],
                    }],
                )
        except (BotoCoreError, ClientError) as e:
            raise ProviderError(f"Failed to put metric: {e}")


# Export public API
__all__ = ["AWSProvider"]