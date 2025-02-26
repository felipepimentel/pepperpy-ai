"""Secure JWT operations for Pepperpy.

This module provides a secure wrapper around python-jose JWT operations with:
- Algorithm restriction to prevent algorithm confusion attacks
- Resource consumption protection
- Additional validation checks
"""

import time
from typing import Any

from jose import JWTError, jwt
from jose.constants import ALGORITHMS

from pepperpy.core.errors.errors import SecurityError


class JWTManager:
    """Secure JWT operations manager."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = ALGORITHMS.ES256,  # Using ES256 by default for better security
        token_ttl: int = 3600,  # 1 hour default TTL
        max_token_size: int = 4096,  # Prevent DoS via large tokens
    ):
        """Initialize the JWT manager.

        Args:
            secret_key: The secret key for JWT operations
            algorithm: The JWT algorithm to use (default: ES256)
            token_ttl: Token time-to-live in seconds (default: 1 hour)
            max_token_size: Maximum token size in bytes (default: 4KB)

        Raises:
            SecurityError: If an unsupported algorithm is specified
        """
        if algorithm not in {ALGORITHMS.ES256, ALGORITHMS.ES384, ALGORITHMS.ES512}:
            raise SecurityError(
                "algorithm",
                algorithm,
                "Only ECDSA algorithms (ES256, ES384, ES512) are supported",
            )

        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_ttl = token_ttl
        self.max_token_size = max_token_size

    def create_token(
        self, data: dict[str, Any], expires_delta: int | None = None
    ) -> str:
        """Create a JWT token.

        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time in seconds

        Returns:
            The encoded JWT token

        Raises:
            SecurityError: If the token would be too large or other security checks fail
        """
        to_encode = data.copy()

        # Add standard claims
        expire = time.time() + (expires_delta or self.token_ttl)
        to_encode.update({
            "exp": expire,  # Expiration time
            "iat": time.time(),  # Issued at
            "nbf": time.time(),  # Not valid before
        })

        try:
            token = jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm,
            )

            # Check token size
            if len(token.encode()) > self.max_token_size:
                raise SecurityError(
                    "token_size",
                    str(len(token.encode())),
                    f"Token size exceeds maximum of {self.max_token_size} bytes",
                )

            return token

        except JWTError as e:
            raise SecurityError("jwt_encode", str(e), "Failed to create JWT token")

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT token.

        Args:
            token: The token to decode

        Returns:
            The decoded token data

        Raises:
            SecurityError: If the token is invalid, expired, or fails security checks
        """
        # Check token size before processing
        if len(token.encode()) > self.max_token_size:
            raise SecurityError(
                "token_size",
                str(len(token.encode())),
                f"Token size exceeds maximum of {self.max_token_size} bytes",
            )

        try:
            # Decode with explicit algorithm verification
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],  # Only allow our specific algorithm
            )

            # Additional validation
            now = time.time()
            if payload.get("exp", 0) < now:
                raise SecurityError("token_expired", "", "Token has expired")
            if payload.get("nbf", 0) > now:
                raise SecurityError("token_not_valid", "", "Token not yet valid")

            return payload

        except JWTError as e:
            raise SecurityError("jwt_decode", str(e), "Failed to decode JWT token")
