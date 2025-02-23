"""Security module.

This module provides security-related functionality.
"""

from pepperpy.security.base import BaseSecurityProvider
from pepperpy.security.decorators import (
    requires_authentication,
    requires_permission,
    requires_role,
    requires_scope,
    requires_scopes,
)
from pepperpy.security.errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DecryptionError,
    DuplicateError,
    EncryptionError,
    RateLimitError,
    SecurityError,
    TokenError,
    ValidationError,
)
from pepperpy.security.provider import SecurityProvider
from pepperpy.security.types import (
    Credentials,
    Permission,
    Policy,
    ProtectionPolicy,
    Role,
    SecurityConfig,
    SecurityContext,
    SecurityScope,
    Token,
)
from pepperpy.security.utils import (
    decrypt_data,
    derive_key,
    encrypt_data,
    generate_salt,
    generate_secret_key,
    generate_token,
    generate_token_id,
    hash_data,
    verify_hash,
    verify_key,
)

__all__ = [
    # Base
    "BaseSecurityProvider",
    # Decorators
    "requires_authentication",
    "requires_permission",
    "requires_role",
    "requires_scope",
    "requires_scopes",
    # Errors
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "DecryptionError",
    "DuplicateError",
    "EncryptionError",
    "RateLimitError",
    "SecurityError",
    "TokenError",
    "ValidationError",
    # Provider
    "SecurityProvider",
    # Types
    "Credentials",
    "Permission",
    "Policy",
    "ProtectionPolicy",
    "Role",
    "SecurityConfig",
    "SecurityContext",
    "SecurityScope",
    "Token",
    # Utils
    "decrypt_data",
    "derive_key",
    "encrypt_data",
    "generate_salt",
    "generate_secret_key",
    "generate_token",
    "generate_token_id",
    "hash_data",
    "verify_hash",
    "verify_key",
]
