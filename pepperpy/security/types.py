"""Security type definitions.

This module provides type definitions for the security system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pepperpy.core.import_utils import import_optional_dependency
from pepperpy.core.models import BaseModel, Field

# Import pydantic safely
pydantic = import_optional_dependency("pydantic", "pydantic>=2.0.0")
if not pydantic:
    raise ImportError("pydantic is required for security types")


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
    permissions: set[Permission] = Field(description="Role permissions")
    description: str | None = Field(default=None, description="Role description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Role metadata")
    resource_patterns: set[str] = Field(
        default_factory=set, description="Resource patterns"
    )


class Credentials(BaseModel):
    """User credentials."""

    user_id: str = Field(description="User ID")
    password: str | None = Field(default=None, description="Password")
    hashed_password: str | None = Field(default=None, description="Hashed password")
    token: str | None = Field(default=None, description="Authentication token")
    mfa_code: str | None = Field(default=None, description="MFA code")
    scopes: set[SecurityScope] = Field(
        default_factory=set, description="Security scopes"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class Token(BaseModel):
    """Authentication token."""

    token_id: UUID = Field(description="Token ID")
    user_id: str = Field(description="User ID")
    scopes: set[SecurityScope] = Field(description="Security scopes")
    issued_at: datetime = Field(description="Token issue time")
    expires_at: datetime = Field(description="Token expiration time")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Token metadata")


class Policy(BaseModel):
    """Security policy."""

    name: str = Field(description="Policy name")
    description: str | None = Field(default=None, description="Policy description")
    roles: set[str] = Field(description="Allowed roles")
    scopes: set[SecurityScope] = Field(description="Required scopes")
    resources: set[str] = Field(description="Protected resources")
    actions: set[Permission] = Field(description="Allowed actions")
    conditions: dict[str, Any] = Field(
        default_factory=dict, description="Policy conditions"
    )


class ProtectionPolicy(BaseModel):
    """Data protection policy."""

    name: str = Field(description="Policy name")
    description: str | None = Field(default=None, description="Policy description")
    field_name: str = Field(description="Protected field name")
    protection_type: str = Field(
        description="Protection type (e.g., encryption, masking)"
    )
    required_scopes: set[SecurityScope] = Field(description="Required scopes")
    encryption_key_id: str | None = Field(default=None, description="Encryption key ID")
    masking_pattern: str | None = Field(default=None, description="Masking pattern")


class SecurityContext(BaseModel):
    """Security context."""

    user_id: str = Field(description="User ID")
    current_token: Token = Field(description="Current token")
    roles: set[str] = Field(description="User roles")
    active_scopes: set[SecurityScope] = Field(description="Active security scopes")
    metadata: dict[str, Any] = Field(
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


class ComponentConfig(BaseModel):
    """Security component configuration.

    Attributes:
        id: Unique identifier
        name: Component name
        type: Component type
        enabled: Whether component is enabled
        config: Additional configuration
    """

    id: UUID = Field(default_factory=uuid4, description="Component ID")
    name: str = Field(description="Component name")
    type: str = Field(description="Component type")
    enabled: bool = Field(default=True, description="Whether component is enabled")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration"
    )

    class Config:
        """Pydantic configuration."""

        validate_assignment = True


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed
        errors: List of validation errors
        warnings: List of validation warnings

    Example:
        >>> result = ValidationResult(
        ...     is_valid=False,
        ...     errors=["Invalid syntax"],
        ...     warnings=["High complexity"]
        ... )
    """

    is_valid: bool
    errors: list[str] | None = None
    warnings: list[str] | None = None
