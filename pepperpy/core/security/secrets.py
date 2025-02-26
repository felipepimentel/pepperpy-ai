"""Secret management functionality.

This module provides classes for managing secrets and their rotation:
1. SecretManager - Handles storage and retrieval of secrets
2. SecretRotator - Handles automatic rotation of secrets
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from pepperpy.core.base import BaseManager
from pepperpy.core.security.crypto import CryptoManager


@dataclass
class Secret:
    """Represents a secret value."""

    secret_id: str
    encrypted_value: bytes
    created_at: datetime = datetime.utcnow()
    expires_at: datetime | None = None
    metadata: dict[str, str] = None

    def is_expired(self) -> bool:
        """Check if the secret has expired."""
        return bool(self.expires_at and datetime.utcnow() > self.expires_at)


class SecretManager(BaseManager):
    """Manages storage and retrieval of secrets."""

    def __init__(self, crypto_manager: CryptoManager | None = None):
        """Initialize the secret manager.

        Args:
            crypto_manager: Optional crypto manager to use. If not provided, a new one will be created.
        """
        super().__init__()
        self._crypto_manager = crypto_manager or CryptoManager()
        self._secrets: dict[str, Secret] = {}

    def store_secret(
        self,
        secret_id: str,
        value: bytes,
        ttl: timedelta | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Secret:
        """Store a secret.

        Args:
            secret_id: Unique identifier for the secret
            value: The secret value to store
            ttl: Optional time-to-live for the secret
            metadata: Optional metadata to store with the secret

        Returns:
            The stored secret

        Raises:
            ValueError: If secret_id already exists
        """
        if secret_id in self._secrets:
            raise ValueError(f"Secret {secret_id} already exists")

        encrypted_value = self._crypto_manager.encrypt(value)
        expires_at = datetime.utcnow() + ttl if ttl else None

        secret = Secret(
            secret_id=secret_id,
            encrypted_value=encrypted_value,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        self._secrets[secret_id] = secret
        return secret

    def get_secret(self, secret_id: str) -> bytes:
        """Get a secret value.

        Args:
            secret_id: The ID of the secret to get

        Returns:
            The decrypted secret value

        Raises:
            KeyError: If secret_id doesn't exist or has expired
        """
        try:
            secret = self._secrets[secret_id]
        except KeyError:
            raise KeyError(f"Secret {secret_id} not found")

        if secret.is_expired():
            del self._secrets[secret_id]
            raise KeyError(f"Secret {secret_id} has expired")

        return self._crypto_manager.decrypt(secret.encrypted_value)

    def delete_secret(self, secret_id: str) -> None:
        """Delete a secret.

        Args:
            secret_id: The ID of the secret to delete
        """
        self._secrets.pop(secret_id, None)

    def list_secrets(self) -> set[str]:
        """List all non-expired secret IDs.

        Returns:
            Set of secret IDs
        """
        return {
            secret_id
            for secret_id, secret in self._secrets.items()
            if not secret.is_expired()
        }


class SecretRotator(BaseManager):
    """Handles automatic rotation of secrets."""

    def __init__(
        self,
        secret_manager: SecretManager | None = None,
        default_ttl: timedelta = timedelta(days=30),
    ):
        """Initialize the secret rotator.

        Args:
            secret_manager: Optional secret manager to use. If not provided, a new one will be created.
            default_ttl: Default time-to-live for rotated secrets
        """
        super().__init__()
        self._secret_manager = secret_manager or SecretManager()
        self._default_ttl = default_ttl
        self._rotation_callbacks: dict[str, callable] = {}

    def register_rotation_callback(
        self, secret_id: str, callback: callable, ttl: timedelta | None = None
    ) -> None:
        """Register a callback for secret rotation.

        The callback should return the new secret value when called.

        Args:
            secret_id: The ID of the secret to rotate
            callback: Function that returns the new secret value
            ttl: Optional time-to-live for the rotated secret
        """
        self._rotation_callbacks[secret_id] = {
            "callback": callback,
            "ttl": ttl or self._default_ttl,
        }

    def rotate_secret(self, secret_id: str) -> Secret:
        """Rotate a secret by generating a new value.

        Args:
            secret_id: The ID of the secret to rotate

        Returns:
            The new secret

        Raises:
            KeyError: If secret_id doesn't exist or has no rotation callback
        """
        if secret_id not in self._rotation_callbacks:
            raise KeyError(f"No rotation callback registered for secret {secret_id}")

        callback_info = self._rotation_callbacks[secret_id]
        new_value = callback_info["callback"]()
        ttl = callback_info["ttl"]

        # Get old secret to preserve metadata
        try:
            old_secret = self._secret_manager._secrets[secret_id]
            metadata = old_secret.metadata
        except KeyError:
            metadata = {}

        # Store new secret
        return self._secret_manager.store_secret(
            secret_id=secret_id, value=new_value, ttl=ttl, metadata=metadata
        )

    def rotate_all_secrets(self) -> dict[str, Secret]:
        """Rotate all secrets that have registered callbacks.

        Returns:
            Dictionary mapping secret IDs to their new secrets
        """
        rotated = {}
        for secret_id in self._rotation_callbacks:
            try:
                rotated[secret_id] = self.rotate_secret(secret_id)
            except Exception as e:
                # Log error but continue rotating other secrets
                print(f"Failed to rotate secret {secret_id}: {e}")
        return rotated
