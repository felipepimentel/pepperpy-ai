"""Encryption utilities for secure data storage.

This module provides encryption utilities using industry standard algorithms
and best practices for secure data storage.
"""

import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class AES256GCM:
    """AES-256-GCM encryption with key derivation."""

    def __init__(self, key: bytes | None = None) -> None:
        """Initialize AES-256-GCM cipher.

        Args:
            key: Optional 32-byte key. If not provided, generates a new one.
        """
        if key is None:
            # Generate a secure random key
            key = os.urandom(32)
        elif len(key) != 32:
            raise ValueError("Key must be 32 bytes")

        self.key = key
        self.aesgcm = AESGCM(key)

    @classmethod
    def from_password(cls, password: str, salt: bytes | None = None) -> "AES256GCM":
        """Create instance from password using PBKDF2.

        Args:
            password: Password to derive key from
            salt: Optional salt. If not provided, generates a new one.

        Returns:
            AES256GCM: New instance with derived key
        """
        if salt is None:
            salt = os.urandom(16)

        # Use PBKDF2 to derive a 32-byte key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        return cls(key)

    async def encrypt(
        self, data: dict[str, Any], associated_data: dict[str, Any] | None = None
    ) -> dict[str, str | None]:
        """Encrypt data with authenticated encryption.

        Args:
            data: Data to encrypt
            associated_data: Optional authenticated data

        Returns:
            Dict[str, Union[str, None]]: Encrypted data with nonce and tag
        """
        # Generate random nonce
        nonce = os.urandom(12)

        # Convert data to bytes
        data_bytes = json.dumps(data).encode()
        aad_bytes = (
            json.dumps(associated_data).encode()
            if associated_data is not None
            else None
        )

        # Encrypt data
        ciphertext = self.aesgcm.encrypt(nonce, data_bytes, aad_bytes)

        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "aad": base64.b64encode(aad_bytes).decode() if aad_bytes else None,
        }

    async def decrypt(self, encrypted_data: dict[str, str]) -> dict[str, Any]:
        """Decrypt data with authentication.

        Args:
            encrypted_data: Encrypted data with nonce and tag

        Returns:
            Dict[str, Any]: Decrypted data

        Raises:
            ValueError: If decryption fails
        """
        try:
            # Decode components
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            nonce = base64.b64decode(encrypted_data["nonce"])
            aad = (
                base64.b64decode(encrypted_data["aad"])
                if encrypted_data.get("aad")
                else None
            )

            # Decrypt data
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, aad)
            return json.loads(plaintext.decode())

        except Exception as e:
            raise ValueError(f"Decryption failed: {e}") from e
