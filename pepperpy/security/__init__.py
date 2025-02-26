"""Security functionality.

This module provides comprehensive security functionality including:
1. Authentication and authorization
2. Encryption and key management
3. Access control and permissions
4. Security auditing and logging
5. Secret management and rotation
"""

from pepperpy.core.security.auth import (
    AuthenticationError,
    AuthenticationManager,
    AuthorizationError,
    AuthorizationManager,
)
from pepperpy.core.security.crypto import (
    CryptoManager,
    DecryptionError,
    EncryptionError,
    KeyManager,
)
from pepperpy.core.security.manager import SecurityManager
from pepperpy.core.security.secrets import SecretManager, SecretRotator

__all__ = [
    # Core components
    "SecurityManager",
    # Authentication
    "AuthenticationManager",
    "AuthenticationError",
    # Authorization
    "AuthorizationManager",
    "AuthorizationError",
    # Encryption
    "CryptoManager",
    "EncryptionError",
    "DecryptionError",
    # Key management
    "KeyManager",
    # Secret management
    "SecretManager",
    "SecretRotator",
]
