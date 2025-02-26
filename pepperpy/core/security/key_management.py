"""Key management system with rotation policy.

This module provides key management functionality with automatic key rotation
and secure storage of encryption keys.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pepperpy.core.errors import ProcessingError, StateError
from pepperpy.core.metrics import MetricsCollector
from pepperpy.security.encryption import AES256GCM
from pepperpy.security.types import SecurityConfig


class KeyRotationPolicy:
    """Key rotation policy configuration."""

    def __init__(
        self,
        rotation_interval: timedelta = timedelta(days=90),
        key_size: int = 32,
        max_active_keys: int = 2,
    ) -> None:
        """Initialize key rotation policy.

        Args:
            rotation_interval: Time interval for key rotation
            key_size: Size of encryption keys in bytes
            max_active_keys: Maximum number of active keys
        """
        self.rotation_interval = rotation_interval
        self.key_size = key_size
        self.max_active_keys = max_active_keys


class EncryptionKey:
    """Encryption key with metadata."""

    def __init__(
        self,
        key_id: UUID,
        key_bytes: bytes,
        created_at: datetime,
        expires_at: datetime,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize encryption key.

        Args:
            key_id: Unique key identifier
            key_bytes: Raw key bytes
            created_at: Creation timestamp
            expires_at: Expiration timestamp
            metadata: Optional key metadata
        """
        self.key_id = key_id
        self.key_bytes = key_bytes
        self.created_at = created_at
        self.expires_at = expires_at
        self.metadata = metadata or {}
        self.cipher = AES256GCM(key_bytes)


class KeyManager:
    """Key management system with rotation."""

    def __init__(
        self,
        config: SecurityConfig,
        metrics: MetricsCollector,
        rotation_policy: Optional[KeyRotationPolicy] = None,
    ) -> None:
        """Initialize key manager.

        Args:
            config: Security configuration
            metrics: Metrics collector
            rotation_policy: Optional key rotation policy
        """
        self.config = config
        self.metrics = metrics
        self.rotation_policy = rotation_policy or KeyRotationPolicy()
        self.active_keys: Dict[UUID, EncryptionKey] = {}
        self.retired_keys: Dict[UUID, EncryptionKey] = {}

        # Initialize metrics
        self.active_keys_gauge = self.metrics.gauge(
            "security_active_keys",
            "Number of active encryption keys",
        )
        self.retired_keys_gauge = self.metrics.gauge(
            "security_retired_keys",
            "Number of retired encryption keys",
        )
        self.key_rotations_counter = self.metrics.counter(
            "security_key_rotations",
            "Number of key rotations performed",
        )

    async def initialize(self) -> None:
        """Initialize key manager and start rotation task."""
        # Generate initial key if none exist
        if not self.active_keys:
            await self.generate_key()

        # Start key rotation task
        asyncio.create_task(self._rotation_task())

    async def generate_key(self) -> EncryptionKey:
        """Generate a new encryption key.

        Returns:
            EncryptionKey: Generated key
        """
        key_id = uuid4()
        key_bytes = os.urandom(self.rotation_policy.key_size)
        created_at = datetime.utcnow()
        expires_at = created_at + self.rotation_policy.rotation_interval

        key = EncryptionKey(
            key_id=key_id,
            key_bytes=key_bytes,
            created_at=created_at,
            expires_at=expires_at,
        )

        self.active_keys[key_id] = key
        self.active_keys_gauge.set(len(self.active_keys))
        return key

    async def get_active_key(self) -> EncryptionKey:
        """Get the most recent active key.

        Returns:
            EncryptionKey: Active encryption key

        Raises:
            StateError: If no active keys are available
        """
        if not self.active_keys:
            raise StateError("No active encryption keys available")

        # Return most recently created key
        return max(
            self.active_keys.values(),
            key=lambda k: k.created_at,
        )

    async def get_key_by_id(self, key_id: UUID) -> EncryptionKey:
        """Get key by ID from active or retired keys.

        Args:
            key_id: Key identifier

        Returns:
            EncryptionKey: Encryption key

        Raises:
            ProcessingError: If key is not found
        """
        key = self.active_keys.get(key_id) or self.retired_keys.get(key_id)
        if not key:
            raise ProcessingError(f"Key {key_id} not found")
        return key

    async def rotate_keys(self) -> None:
        """Perform key rotation."""
        # Generate new key
        new_key = await self.generate_key()

        # Retire expired keys
        now = datetime.utcnow()
        expired = [
            key_id
            for key_id, key in self.active_keys.items()
            if key.expires_at <= now
        ]

        for key_id in expired:
            key = self.active_keys.pop(key_id)
            self.retired_keys[key_id] = key

        # Update metrics
        self.active_keys_gauge.set(len(self.active_keys))
        self.retired_keys_gauge.set(len(self.retired_keys))
        self.key_rotations_counter.inc()

    async def _rotation_task(self) -> None:
        """Background task for automatic key rotation."""
        while True:
            try:
                # Sleep until next rotation
                active_key = await self.get_active_key()
                sleep_time = (
                    active_key.expires_at - datetime.utcnow()
                ).total_seconds()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

                # Perform rotation
                await self.rotate_keys()

            except Exception as e:
                # Log error but continue running
                print(f"Key rotation error: {e}")
                await asyncio.sleep(60)  # Retry after delay 