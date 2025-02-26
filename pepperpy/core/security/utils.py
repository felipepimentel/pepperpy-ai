"""Security utilities.

This module provides utility functions for security-related operations.
"""

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set, Union
from uuid import UUID, uuid4

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pepperpy.security.errors import EncryptionError
from pepperpy.security.types import SecurityScope, Token


def generate_token_id() -> UUID:
    """Generate token ID.

    Returns:
        Token ID
    """
    return uuid4()


def generate_token(
    user_id: str,
    scopes: Optional[Set[SecurityScope]] = None,
    expiration: Optional[timedelta] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Token:
    """Generate authentication token.

    Args:
        user_id: User ID
        scopes: Security scopes
        expiration: Token expiration
        metadata: Token metadata

    Returns:
        Authentication token
    """
    now = datetime.utcnow()
    return Token(
        token_id=generate_token_id(),
        user_id=user_id,
        scopes=scopes or set(),
        issued_at=now,
        expires_at=now + (expiration or timedelta(days=1)),
        metadata=metadata or {},
    )


def generate_secret_key(length: int = 32) -> bytes:
    """Generate secret key.

    Args:
        length: Key length in bytes

    Returns:
        Secret key
    """
    return secrets.token_bytes(length)


def generate_salt(length: int = 16) -> bytes:
    """Generate salt.

    Args:
        length: Salt length in bytes

    Returns:
        Salt
    """
    return os.urandom(length)


def derive_key(
    password: Union[str, bytes],
    salt: bytes,
    length: int = 32,
    iterations: int = 100000,
) -> bytes:
    """Derive encryption key from password.

    Args:
        password: Password
        salt: Salt
        length: Key length in bytes
        iterations: Number of iterations

    Returns:
        Derived key
    """
    if isinstance(password, str):
        password = password.encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password)


def verify_key(
    password: Union[str, bytes],
    salt: bytes,
    key: bytes,
    iterations: int = 100000,
) -> bool:
    """Verify encryption key.

    Args:
        password: Password
        salt: Salt
        key: Key to verify
        iterations: Number of iterations

    Returns:
        True if key is valid
    """
    if isinstance(password, str):
        password = password.encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=len(key),
        salt=salt,
        iterations=iterations,
    )
    try:
        kdf.verify(password, key)
        return True
    except Exception:
        return False


def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt data.

    Args:
        data: Data to encrypt
        key: Encryption key

    Returns:
        Encrypted data

    Raises:
        EncryptionError: If encryption fails
    """
    try:
        fernet = Fernet(base64.urlsafe_b64encode(key))
        return fernet.encrypt(data)
    except Exception as e:
        raise EncryptionError(f"Failed to encrypt data: {e}")


def decrypt_data(data: bytes, key: bytes) -> bytes:
    """Decrypt data.

    Args:
        data: Data to decrypt
        key: Encryption key

    Returns:
        Decrypted data

    Raises:
        DecryptionError: If decryption fails
    """
    try:
        fernet = Fernet(base64.urlsafe_b64encode(key))
        return fernet.decrypt(data)
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt data: {e}")


def hash_data(data: Union[str, bytes], salt: Optional[bytes] = None) -> bytes:
    """Hash data.

    Args:
        data: Data to hash
        salt: Optional salt

    Returns:
        Hashed data
    """
    if isinstance(data, str):
        data = data.encode()

    if salt:
        data = salt + data

    return hashlib.sha256(data).digest()


def verify_hash(
    data: Union[str, bytes], hashed: bytes, salt: Optional[bytes] = None
) -> bool:
    """Verify hash.

    Args:
        data: Data to verify
        hashed: Hash to verify against
        salt: Optional salt

    Returns:
        True if hash is valid
    """
    if isinstance(data, str):
        data = data.encode()

    if salt:
        data = salt + data

    return hmac.compare_digest(hashlib.sha256(data).digest(), hashed)
