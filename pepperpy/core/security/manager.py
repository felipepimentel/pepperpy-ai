"""Security manager.

This module provides the main security manager that coordinates all security functionality:
1. Authentication and authorization
2. Encryption and key management
3. Secret management and rotation
4. Security auditing and logging
"""

from dataclasses import dataclass
from datetime import timedelta

from pepperpy.core.base import BaseManager
from pepperpy.core.security.auth import AuthenticationManager, AuthorizationManager
from pepperpy.core.security.crypto import CryptoManager, KeyManager
from pepperpy.core.security.secrets import SecretManager, SecretRotator
from pepperpy.core.types import UserId


@dataclass
class SecurityConfig:
    """Security configuration."""

    session_timeout: timedelta = timedelta(hours=1)
    secret_rotation_interval: timedelta = timedelta(days=30)
    audit_log_retention: timedelta = timedelta(days=90)
    enable_key_rotation: bool = True
    enable_secret_rotation: bool = True
    enable_audit_logging: bool = True


class SecurityManager(BaseManager):
    """Manages all security functionality."""

    def __init__(self, config: SecurityConfig | None = None):
        """Initialize the security manager.

        Args:
            config: Optional security configuration
        """
        super().__init__()
        self._config = config or SecurityConfig()

        # Initialize components
        self._key_manager = KeyManager()
        self._crypto_manager = CryptoManager(self._key_manager)
        self._auth_manager = AuthenticationManager(self._config.session_timeout)
        self._authz_manager = AuthorizationManager()
        self._secret_manager = SecretManager(self._crypto_manager)
        self._secret_rotator = SecretRotator(
            self._secret_manager, self._config.secret_rotation_interval
        )

    def authenticate(self, user_id: UserId, scopes: set[str] | None = None) -> str:
        """Authenticate a user.

        Args:
            user_id: The ID of the user to authenticate
            scopes: Optional set of scopes to grant

        Returns:
            The session token
        """
        return self._auth_manager.authenticate(user_id, scopes)

    def validate_session(self, token: str) -> bool:
        """Validate a session token.

        Args:
            token: The session token to validate

        Returns:
            True if the token is valid, False otherwise
        """
        try:
            self._auth_manager.validate_session(token)
            return True
        except Exception:
            return False

    def check_permission(self, user_id: UserId, permission: str) -> bool:
        """Check if a user has a permission.

        Args:
            user_id: The user to check
            permission: The permission to check for

        Returns:
            True if the user has the permission, False otherwise
        """
        return self._authz_manager.check_permission(user_id, permission)

    def store_secret(
        self,
        secret_id: str,
        value: bytes,
        ttl: timedelta | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Store a secret.

        Args:
            secret_id: Unique identifier for the secret
            value: The secret value to store
            ttl: Optional time-to-live for the secret
            metadata: Optional metadata to store with the secret
        """
        self._secret_manager.store_secret(secret_id, value, ttl, metadata)

    def get_secret(self, secret_id: str) -> bytes:
        """Get a secret value.

        Args:
            secret_id: The ID of the secret to get

        Returns:
            The decrypted secret value
        """
        return self._secret_manager.get_secret(secret_id)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data.

        Args:
            data: The data to encrypt

        Returns:
            The encrypted data
        """
        return self._crypto_manager.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data.

        Args:
            encrypted_data: The data to decrypt

        Returns:
            The decrypted data
        """
        return self._crypto_manager.decrypt(encrypted_data)

    def rotate_keys(self) -> None:
        """Rotate all cryptographic keys."""
        if not self._config.enable_key_rotation:
            return

        for key_id in list(self._key_manager._keys.keys()):
            self._key_manager.rotate_key(key_id)

    def rotate_secrets(self) -> None:
        """Rotate all secrets."""
        if not self._config.enable_secret_rotation:
            return

        self._secret_rotator.rotate_all_secrets()

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        self._auth_manager.cleanup()
        self._authz_manager.cleanup()
        self._secret_manager.cleanup()
        self._secret_rotator.cleanup()
