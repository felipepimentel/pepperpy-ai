"""Cryptographic functionality.

This module provides classes for encryption, key management and cryptographic operations:
1. CryptoManager - Handles encryption and decryption operations
2. KeyManager - Handles cryptographic key management
"""

import base64
import os
from dataclasses import dataclass
from datetime import datetime

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pepperpy.core.common.base import BaseManager


class EncryptionError(Exception):
    """Raised when encryption fails."""

    pass


class DecryptionError(Exception):
    """Raised when decryption fails."""

    pass


@dataclass
class Key:
    """Represents a cryptographic key."""

    key_id: str
    key_bytes: bytes
    created_at: datetime = datetime.utcnow()
    expires_at: datetime | None = None
    metadata: dict[str, str] = None

    def is_expired(self) -> bool:
        """Check if the key has expired."""
        return bool(self.expires_at and datetime.utcnow() > self.expires_at)


class KeyManager(BaseManager):
    """Manages cryptographic keys."""

    def __init__(self):
        """Initialize the key manager."""
        super().__init__()
        self._keys: dict[str, Key] = {}
        self._active_key_id: str | None = None

    def create_key(self, key_id: str, metadata: dict[str, str] | None = None) -> Key:
        """Create a new cryptographic key.

        Args:
            key_id: Unique identifier for the key
            metadata: Optional metadata to store with the key

        Returns:
            The created key

        Raises:
            ValueError: If key_id already exists
        """
        if key_id in self._keys:
            raise ValueError(f"Key {key_id} already exists")

        key_bytes = Fernet.generate_key()
        key = Key(key_id=key_id, key_bytes=key_bytes, metadata=metadata or {})
        self._keys[key_id] = key

        if not self._active_key_id:
            self._active_key_id = key_id

        return key

    def get_key(self, key_id: str) -> Key:
        """Get a key by its ID.

        Args:
            key_id: The ID of the key to get

        Returns:
            The key

        Raises:
            KeyError: If key_id doesn't exist
        """
        try:
            key = self._keys[key_id]
        except KeyError:
            raise KeyError(f"Key {key_id} not found")

        if key.is_expired():
            raise KeyError(f"Key {key_id} has expired")

        return key

    def rotate_key(self, key_id: str) -> Key:
        """Rotate a key by creating a new one and marking the old one as expired.

        Args:
            key_id: The ID of the key to rotate

        Returns:
            The new key

        Raises:
            KeyError: If key_id doesn't exist
        """
        old_key = self.get_key(key_id)
        old_key.expires_at = datetime.utcnow()

        new_key_id = f"{key_id}_rotated_{datetime.utcnow().timestamp()}"
        return self.create_key(new_key_id, old_key.metadata)

    def set_active_key(self, key_id: str) -> None:
        """Set the active key for encryption operations.

        Args:
            key_id: The ID of the key to set as active

        Raises:
            KeyError: If key_id doesn't exist
        """
        # Verify key exists and is valid
        self.get_key(key_id)
        self._active_key_id = key_id

    def get_active_key(self) -> Key:
        """Get the currently active key.

        Returns:
            The active key

        Raises:
            RuntimeError: If no active key is set
        """
        if not self._active_key_id:
            raise RuntimeError("No active key set")
        return self.get_key(self._active_key_id)


class CryptoManager(BaseManager):
    """Manages encryption and decryption operations."""

    def __init__(self, key_manager: KeyManager | None = None):
        """Initialize the crypto manager.

        Args:
            key_manager: Optional key manager to use. If not provided, a new one will be created.
        """
        super().__init__()
        self._key_manager = key_manager or KeyManager()
        self._fernet = None

    def _get_fernet(self) -> Fernet:
        """Get or create the Fernet instance using the active key."""
        active_key = self._key_manager.get_active_key()
        return Fernet(active_key.key_bytes)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using the active key.

        Args:
            data: The data to encrypt

        Returns:
            The encrypted data

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            return self._get_fernet().encrypt(data)
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using the active key.

        Args:
            encrypted_data: The data to decrypt

        Returns:
            The decrypted data

        Raises:
            DecryptionError: If decryption fails
        """
        try:
            return self._get_fernet().decrypt(encrypted_data)
        except Exception as e:
            raise DecryptionError(f"Failed to decrypt data: {e}")

    def derive_key(self, password: str, salt: bytes | None = None) -> bytes:
        """Derive a key from a password using PBKDF2.

        Args:
            password: The password to derive the key from
            salt: Optional salt to use. If not provided, a random one will be generated.

        Returns:
            The derived key
        """
        salt = salt or os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
