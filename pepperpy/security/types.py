"""Security type definitions.

This module provides type definitions for the security system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field


class SecurityScope(str, Enum):
    """Security scope enumeration."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    EXECUTE = "execute"


class Permission(str, Enum):
    """Permission enumeration."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class Role(BaseModel):
    """Role definition."""

    name: str = Field(description="Role name")
    permissions: Set[Permission] = Field(description="Role permissions")
    description: Optional[str] = Field(default=None, description="Role description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Role metadata")


class Credentials(BaseModel):
    """User credentials."""

    user_id: str = Field(description="User ID")
    password: Optional[str] = Field(default=None, description="Password")
    token: Optional[str] = Field(default=None, description="Authentication token")
    mfa_code: Optional[str] = Field(default=None, description="MFA code")
    scopes: Set[SecurityScope] = Field(
        default_factory=set, description="Security scopes"
    )


class Token(BaseModel):
    """Authentication token."""

    token_id: UUID = Field(description="Token ID")
    user_id: str = Field(description="User ID")
    scopes: Set[SecurityScope] = Field(description="Security scopes")
    issued_at: datetime = Field(description="Token issue time")
    expires_at: datetime = Field(description="Token expiration time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Token metadata")


class Policy(BaseModel):
    """Security policy."""

    name: str = Field(description="Policy name")
    description: Optional[str] = Field(default=None, description="Policy description")
    roles: Set[str] = Field(description="Allowed roles")
    scopes: Set[SecurityScope] = Field(description="Required scopes")
    resources: Set[str] = Field(description="Protected resources")
    actions: Set[Permission] = Field(description="Allowed actions")
    conditions: Dict[str, Any] = Field(
        default_factory=dict, description="Policy conditions"
    )


class ProtectionPolicy(BaseModel):
    """Data protection policy."""

    name: str = Field(description="Policy name")
    description: Optional[str] = Field(default=None, description="Policy description")
    field_name: str = Field(description="Protected field name")
    protection_type: str = Field(
        description="Protection type (e.g., encryption, masking)"
    )
    required_scopes: Set[SecurityScope] = Field(description="Required scopes")
    encryption_key_id: Optional[str] = Field(
        default=None, description="Encryption key ID"
    )
    masking_pattern: Optional[str] = Field(default=None, description="Masking pattern")


class SecurityContext(BaseModel):
    """Security context."""

    user_id: str = Field(description="User ID")
    current_token: Token = Field(description="Current token")
    roles: Set[str] = Field(description="User roles")
    active_scopes: Set[SecurityScope] = Field(description="Active security scopes")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Context metadata"
    )


class SecurityConfig(BaseModel):
    """Security configuration."""

    min_password_length: int = Field(default=8, description="Minimum password length")
    require_mfa: bool = Field(default=False, description="Require MFA")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    token_expiration: int = Field(
        default=86400, description="Token expiration in seconds"
    )
    max_login_attempts: int = Field(default=3, description="Maximum login attempts")
    password_history: int = Field(default=3, description="Password history size")
    encryption_algorithm: str = Field(
        default="AES-256-GCM", description="Encryption algorithm"
    )
    hash_algorithm: str = Field(default="bcrypt", description="Password hash algorithm")

    class Config:
        """Pydantic configuration."""

        env_prefix = "PEPPERPY_SECURITY_"
        validate_assignment = True
