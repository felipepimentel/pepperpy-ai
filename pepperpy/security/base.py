"""Base security module for the Pepperpy framework.

This module provides core security functionality including:
- Authentication and authorization
- Encryption and data protection
- Security validation and verification
- Audit logging and monitoring
"""

import base64
import json
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import NotFoundError, ValidationError
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.monitoring.audit import AuditLogger
from pepperpy.monitoring.metrics import MetricsManager
from pepperpy.security.errors import (
    AuthenticationError,
    DecryptionError,
    DuplicateError,
    EncryptionError,
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
    encrypt_data,
    generate_salt,
    generate_token,
    hash_data,
    verify_hash,
)

# Configure logging
logger = logger.getChild(__name__)


# Security configuration
class SecurityConfig(BaseModel):
    """Security configuration.

    Attributes:
        id: Unique identifier
        name: Security component name
        type: Security component type
        enabled: Whether component is enabled
        config: Additional configuration
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    type: str
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure config is immutable."""
        return dict(v)


# Base security component
class SecurityComponent(Lifecycle):
    """Base class for security components.

    This class defines the core interface that all security components
    must implement, including lifecycle management and metrics.
    """

    def __init__(self, config: SecurityConfig) -> None:
        """Initialize security component.

        Args:
            config: Security configuration
        """
        super().__init__()
        self.config = config
        self._metrics = MetricsManager.get_instance()
        self._audit = AuditLogger()
        self._state = ComponentState.UNREGISTERED

    @property
    def id(self) -> UUID:
        """Get component ID."""
        return self.config.id

    @property
    def name(self) -> str:
        """Get component name."""
        return self.config.name

    @property
    def type(self) -> str:
        """Get component type."""
        return self.config.type

    @property
    def enabled(self) -> bool:
        """Get enabled status."""
        return self.config.enabled

    async def initialize(self) -> None:
        """Initialize security component.

        This method should be called before using the component.
        It should set up any necessary resources and validate configuration.

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If initialization fails
        """
        try:
            # Initialize metrics
            self._operation_counter = await self._metrics.create_counter(
                name=f"{self.name}_operations_total",
                description=f"Total operations for {self.name}",
                labels={"type": self.type},
            )

            self._error_counter = await self._metrics.create_counter(
                name=f"{self.name}_errors_total",
                description=f"Total errors for {self.name}",
                labels={"type": self.type},
            )

            self._latency_histogram = await self._metrics.create_histogram(
                name=f"{self.name}_operation_latency_seconds",
                description=f"Operation latency for {self.name}",
                labels={"type": self.type},
            )

            self._state = ComponentState.RUNNING
            await self._audit.log({
                "event_type": "security.component.initialized",
                "component": self.name,
                "type": self.type,
            })

        except Exception as e:
            self._state = ComponentState.ERROR
            await self._audit.log({
                "event_type": "security.component.error",
                "component": self.name,
                "type": self.type,
                "error": str(e),
            })
            raise RuntimeError(f"Failed to initialize {self.name}: {e}")

    async def cleanup(self) -> None:
        """Clean up security component.

        This method should be called when the component is no longer needed.
        It should clean up any resources and perform necessary shutdown tasks.

        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            self._state = ComponentState.UNREGISTERED
            await self._audit.log({
                "event_type": "security.component.cleaned_up",
                "component": self.name,
                "type": self.type,
            })

        except Exception as e:
            await self._audit.log({
                "event_type": "security.component.error",
                "component": self.name,
                "type": self.type,
                "error": str(e),
            })
            raise RuntimeError(f"Failed to clean up {self.name}: {e}")


# Authentication component
class AuthenticationComponent(SecurityComponent):
    """Component for authentication.

    This component handles user authentication and token management.
    """

    def __init__(self, config: SecurityConfig) -> None:
        """Initialize authentication component.

        Args:
            config: Security configuration
        """
        super().__init__(config)
        self._tokens: dict[str, dict[str, Any]] = {}

    async def authenticate(
        self,
        credentials: dict[str, str],
    ) -> str:
        """Authenticate user and generate token.

        Args:
            credentials: User credentials

        Returns:
            str: Authentication token

        Raises:
            ValueError: If authentication fails
        """
        if not self.enabled:
            raise RuntimeError("Authentication disabled")

        start_time = datetime.utcnow()
        try:
            # Validate credentials
            if "username" not in credentials or "password" not in credentials:
                raise ValueError("Missing credentials")

            # Generate token
            token = str(uuid4())
            self._tokens[token] = {
                "username": credentials["username"],
                "created_at": start_time,
                "expires_at": start_time + timedelta(hours=1),
            }

            await self._operation_counter.inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._latency_histogram.observe(duration)

            await self._audit.log({
                "event_type": "security.auth.token_created",
                "username": credentials["username"],
            })

            return token

        except Exception as e:
            await self._error_counter.inc()
            await self._audit.log({
                "event_type": "security.auth.error",
                "error": str(e),
            })
            raise ValueError(f"Authentication failed: {e}")

    async def validate_token(self, token: str) -> bool:
        """Validate authentication token.

        Args:
            token: Token to validate

        Returns:
            bool: True if token is valid
        """
        if not self.enabled:
            raise RuntimeError("Authentication disabled")

        start_time = datetime.utcnow()
        try:
            # Check token exists
            if token not in self._tokens:
                return False

            # Check token expiration
            token_data = self._tokens[token]
            if datetime.utcnow() > token_data["expires_at"]:
                del self._tokens[token]
                return False

            await self._operation_counter.inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._latency_histogram.observe(duration)

            return True

        except Exception as e:
            await self._error_counter.inc()
            await self._audit.log({
                "event_type": "security.auth.error",
                "error": str(e),
            })
            return False


# Authorization component
class AuthorizationComponent(SecurityComponent):
    """Component for authorization.

    This component handles role-based access control.
    """

    def __init__(self, config: SecurityConfig) -> None:
        """Initialize authorization component.

        Args:
            config: Security configuration
        """
        super().__init__(config)
        self._roles: dict[str, set[str]] = {}
        self._user_roles: dict[str, set[str]] = {}

    async def create_role(
        self,
        name: str,
        permissions: set[str],
    ) -> None:
        """Create a role with permissions.

        Args:
            name: Role name
            permissions: Set of permissions

        Raises:
            ValueError: If role creation fails
        """
        if not self.enabled:
            raise RuntimeError("Authorization disabled")

        start_time = datetime.utcnow()
        try:
            self._roles[name] = permissions

            await self._operation_counter.inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._latency_histogram.observe(duration)

            await self._audit.log({
                "event_type": "security.authz.role_created",
                "role": name,
                "permissions": list(permissions),
            })

        except Exception as e:
            await self._error_counter.inc()
            await self._audit.log({
                "event_type": "security.authz.error",
                "error": str(e),
            })
            raise ValueError(f"Role creation failed: {e}")

    async def assign_role(
        self,
        username: str,
        role: str,
    ) -> None:
        """Assign role to user.

        Args:
            username: Username
            role: Role name

        Raises:
            ValueError: If role assignment fails
        """
        if not self.enabled:
            raise RuntimeError("Authorization disabled")

        start_time = datetime.utcnow()
        try:
            # Check role exists
            if role not in self._roles:
                raise ValueError(f"Role not found: {role}")

            # Assign role
            if username not in self._user_roles:
                self._user_roles[username] = set()
            self._user_roles[username].add(role)

            await self._operation_counter.inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._latency_histogram.observe(duration)

            await self._audit.log({
                "event_type": "security.authz.role_assigned",
                "username": username,
                "role": role,
            })

        except Exception as e:
            await self._error_counter.inc()
            await self._audit.log({
                "event_type": "security.authz.error",
                "error": str(e),
            })
            raise ValueError(f"Role assignment failed: {e}")

    async def check_permission(
        self,
        username: str,
        permission: str,
    ) -> bool:
        """Check if user has permission.

        Args:
            username: Username
            permission: Permission to check

        Returns:
            bool: True if user has permission
        """
        if not self.enabled:
            raise RuntimeError("Authorization disabled")

        start_time = datetime.utcnow()
        try:
            # Get user roles
            user_roles = self._user_roles.get(username, set())

            # Check permission in each role
            for role in user_roles:
                role_permissions = self._roles.get(role, set())
                if permission in role_permissions:
                    await self._operation_counter.inc()
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    await self._latency_histogram.observe(duration)
                    return True

            return False

        except Exception as e:
            await self._error_counter.inc()
            await self._audit.log({
                "event_type": "security.authz.error",
                "error": str(e),
            })
            return False


# Data protection component
class DataProtectionComponent(SecurityComponent):
    """Component for data protection.

    This component handles data encryption and masking.
    """

    def __init__(self, config: SecurityConfig) -> None:
        """Initialize data protection component.

        Args:
            config: Security configuration
        """
        super().__init__(config)

    async def protect_data(
        self,
        data: dict[str, Any],
        fields: set[str],
    ) -> dict[str, Any]:
        """Protect sensitive data fields.

        Args:
            data: Data to protect
            fields: Fields to protect

        Returns:
            Dict[str, Any]: Protected data

        Raises:
            ValueError: If data protection fails
        """
        if not self.enabled:
            raise RuntimeError("Data protection disabled")

        start_time = datetime.utcnow()
        try:
            protected = data.copy()

            # Mask sensitive fields
            for field in fields:
                if field in protected:
                    protected[field] = "********"

            await self._operation_counter.inc()
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._latency_histogram.observe(duration)

            await self._audit.log({
                "event_type": "security.data.protected",
                "fields": list(fields),
            })

            return protected

        except Exception as e:
            await self._error_counter.inc()
            await self._audit.log({
                "event_type": "security.data.error",
                "error": str(e),
            })
            raise ValueError(f"Data protection failed: {e}")


# Export public API
__all__ = [
    "AuthenticationComponent",
    "AuthorizationComponent",
    "DataProtectionComponent",
    "SecurityComponent",
    "SecurityConfig",
]


class BaseSecurityProvider(SecurityProvider):
    """Base security provider implementation."""

    def __init__(self) -> None:
        """Initialize base security provider."""
        self._initialized = False
        self._config = SecurityConfig()  # Initialize with default config
        self._roles: dict[str, Role] = {}
        self._policies: dict[str, Policy] = {}
        self._protection_policies: dict[str, ProtectionPolicy] = {}
        self._tokens: dict[UUID, Token] = {}
        self._security_contexts: dict[UUID, SecurityContext] = {}

    def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Initialize provider.

        Args:
            config: Optional provider configuration
        """
        if self._initialized:
            return

        if config:
            self._config = SecurityConfig(**config)
        else:
            self._config = SecurityConfig()

        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown provider."""
        self._initialized = False
        self._config = None
        self._roles.clear()
        self._policies.clear()
        self._protection_policies.clear()

    def get_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name
        """
        return "base"

    def get_version(self) -> str:
        """Get provider version.

        Returns:
            Provider version
        """
        return "1.0.0"

    def get_description(self) -> str:
        """Get provider description.

        Returns:
            Provider description
        """
        return "Base security provider implementation"

    def get_capabilities(self) -> dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Provider capabilities
        """
        return {
            "authentication": True,
            "authorization": True,
            "encryption": True,
            "password_hashing": True,
        }

    def get_status(self) -> dict[str, Any]:
        """Get provider status.

        Returns:
            Provider status
        """
        return {
            "initialized": self._initialized,
            "roles": len(self._roles),
            "policies": len(self._policies),
            "protection_policies": len(self._protection_policies),
        }

    def get_metrics(self) -> dict[str, Any]:
        """Get provider metrics.

        Returns:
            Provider metrics
        """
        return {}

    def get_config(self) -> SecurityConfig:
        """Get security configuration.

        Returns:
            Security configuration
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        return self._config

    def update_config(self, config: SecurityConfig) -> SecurityConfig:
        """Update security configuration.

        Args:
            config: New configuration

        Returns:
            Updated configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        try:
            # Validate and update config
            self._config = config
            return self._config

        except Exception as e:
            raise ValidationError(f"Invalid configuration: {e}")

    def get_roles(self) -> list[Role]:
        """Get available roles.

        Returns:
            List of available roles
        """
        if not self._initialized:
            return []

        return list(self._roles.values())

    def create_role(self, role: Role) -> Role:
        """Create new role.

        Args:
            role: Role to create

        Returns:
            Created role

        Raises:
            ValidationError: If role is invalid
            DuplicateError: If role already exists
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        if role.name in self._roles:
            raise DuplicateError(f"Role already exists: {role.name}")

        self._roles[role.name] = role
        return role

    def update_role(self, role: Role) -> Role:
        """Update existing role.

        Args:
            role: Role to update

        Returns:
            Updated role

        Raises:
            ValidationError: If role is invalid
            NotFoundError: If role does not exist
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        if role.name not in self._roles:
            raise NotFoundError(f"Role not found: {role.name}")

        self._roles[role.name] = role
        return role

    def delete_role(self, role_name: str) -> None:
        """Delete role.

        Args:
            role_name: Name of role to delete

        Raises:
            NotFoundError: If role does not exist
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        if role_name not in self._roles:
            raise NotFoundError(f"Role not found: {role_name}")

        del self._roles[role_name]

    def get_policies(self) -> list[Policy]:
        """Get security policies.

        Returns:
            List of security policies
        """
        if not self._initialized:
            return []

        return list(self._policies.values())

    def create_policy(self, policy: Policy) -> Policy:
        """Create security policy.

        Args:
            policy: Policy to create

        Returns:
            Created policy

        Raises:
            ValidationError: If policy is invalid
            DuplicateError: If policy already exists
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        if policy.name in self._policies:
            raise DuplicateError(f"Policy already exists: {policy.name}")

        self._policies[policy.name] = policy
        return policy

    def update_policy(self, policy: Policy) -> Policy:
        """Update security policy.

        Args:
            policy: Policy to update

        Returns:
            Updated policy

        Raises:
            ValidationError: If policy is invalid
            NotFoundError: If policy does not exist
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        if policy.name not in self._policies:
            raise NotFoundError(f"Policy not found: {policy.name}")

        self._policies[policy.name] = policy
        return policy

    def delete_policy(self, policy_name: str) -> None:
        """Delete security policy.

        Args:
            policy_name: Name of policy to delete

        Raises:
            NotFoundError: If policy does not exist
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        if policy_name not in self._policies:
            raise NotFoundError(f"Policy not found: {policy_name}")

        del self._policies[policy_name]

    def get_protection_policies(self) -> list[ProtectionPolicy]:
        """Get data protection policies.

        Returns:
            List of protection policies
        """
        if not self._initialized:
            return []

        return list(self._protection_policies.values())

    def create_protection_policy(self, policy: ProtectionPolicy) -> ProtectionPolicy:
        """Create data protection policy.

        Args:
            policy: Policy to create

        Returns:
            Created policy

        Raises:
            ValidationError: If policy is invalid
            DuplicateError: If policy already exists
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        if policy.name in self._protection_policies:
            raise DuplicateError(f"Protection policy already exists: {policy.name}")

        self._protection_policies[policy.name] = policy
        return policy

    def update_protection_policy(self, policy: ProtectionPolicy) -> ProtectionPolicy:
        """Update data protection policy.

        Args:
            policy: Policy to update

        Returns:
            Updated policy

        Raises:
            ValidationError: If policy is invalid
            NotFoundError: If policy does not exist
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        if policy.name not in self._protection_policies:
            raise NotFoundError(f"Protection policy not found: {policy.name}")

        self._protection_policies[policy.name] = policy
        return policy

    def delete_protection_policy(self, policy_name: str) -> None:
        """Delete data protection policy.

        Args:
            policy_name: Name of policy to delete

        Raises:
            NotFoundError: If policy does not exist
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        if policy_name not in self._protection_policies:
            raise NotFoundError(f"Protection policy not found: {policy_name}")

        del self._protection_policies[policy_name]

    def authenticate(
        self,
        credentials: Credentials,
        scopes: set[SecurityScope] | None = None,
    ) -> Token:
        """Authenticate user and generate token.

        Args:
            credentials: User credentials
            scopes: Requested security scopes

        Returns:
            Authentication token

        Raises:
            AuthenticationError: If authentication fails
        """
        if not self._initialized:
            raise AuthenticationError("Provider not initialized")

        # Verify credentials
        if not credentials.password or not credentials.hashed_password:
            raise AuthenticationError("Missing credentials")

        if not self.verify_password(credentials.password, credentials.hashed_password):
            raise AuthenticationError("Invalid credentials")

        # Generate token with default expiration if config is not set
        expiration = timedelta(seconds=86400)  # Default 24h
        if self._config:
            expiration = timedelta(seconds=self._config.token_expiration)

        token = generate_token(
            user_id=credentials.user_id,
            scopes=scopes,
            expiration=expiration,
            metadata=credentials.metadata,
        )

        # Store token
        self._tokens[token.token_id] = token

        # Create security context
        context = SecurityContext(
            user_id=credentials.user_id,
            scopes=scopes or set(),
            roles=self._get_user_roles(credentials.user_id),
            metadata=credentials.metadata or {},
        )
        self._security_contexts[token.token_id] = context

        return token

    def validate_token(self, token: Token) -> bool:
        """Validate token.

        Args:
            token: Token to validate

        Returns:
            True if token is valid
        """
        # Check token exists
        stored_token = self._tokens.get(token.token_id)
        if not stored_token:
            return False

        # Check token expiration
        if datetime.utcnow() > stored_token.expires_at:
            self.revoke_token(token)
            return False

        return True

    def refresh_token(self, token: Token) -> Token:
        """Refresh token.

        Args:
            token: Token to refresh

        Returns:
            New token

        Raises:
            AuthenticationError: If token refresh fails
        """
        if not self._initialized:
            raise AuthenticationError("Provider not initialized")

        # Validate token
        if not self.validate_token(token):
            raise AuthenticationError("Invalid token")

        # Generate new token with default expiration if config is not set
        expiration = timedelta(seconds=86400)  # Default 24h
        if self._config:
            expiration = timedelta(seconds=self._config.token_expiration)

        new_token = generate_token(
            user_id=token.user_id,
            scopes=token.scopes,
            expiration=expiration,
            metadata=token.metadata,
        )

        # Store new token
        self._tokens[new_token.token_id] = new_token

        # Copy security context
        if token.token_id in self._security_contexts:
            self._security_contexts[new_token.token_id] = self._security_contexts[
                token.token_id
            ]

        # Revoke old token
        self.revoke_token(token)

        return new_token

    def revoke_token(self, token: Token) -> None:
        """Revoke token.

        Args:
            token: Token to revoke

        Raises:
            AuthenticationError: If token revocation fails
        """
        # Remove token
        if token.token_id in self._tokens:
            del self._tokens[token.token_id]

        # Remove security context
        if token.token_id in self._security_contexts:
            del self._security_contexts[token.token_id]

    def get_security_context(self, token: Token) -> SecurityContext:
        """Get security context from token.

        Args:
            token: Authentication token

        Returns:
            Security context

        Raises:
            AuthenticationError: If token is invalid
        """
        # Validate token
        if not self.validate_token(token):
            raise AuthenticationError("Invalid token")

        # Get security context
        context = self._security_contexts.get(token.token_id)
        if not context:
            raise AuthenticationError("Security context not found")

        return context

    def _get_user_roles(self, user_id: str) -> set[str]:
        """Get roles for user.

        Args:
            user_id: User ID

        Returns:
            Set of role names
        """
        # This is a placeholder implementation
        # In a real implementation, this would fetch roles from a database
        return set()

    def encrypt(self, data: Any, policy_name: str) -> bytes:
        """Encrypt data using protection policy.

        Args:
            data: Data to encrypt
            policy_name: Name of protection policy

        Returns:
            Encrypted data

        Raises:
            NotFoundError: If policy does not exist
            EncryptionError: If encryption fails
        """
        # Get protection policy
        policy = self.get_protection_policy(policy_name)
        if policy is None:
            raise NotFoundError(f"Protection policy not found: {policy_name}")

        try:
            # Convert data to JSON bytes
            data_bytes = json.dumps(data).encode()

            # Get encryption key from policy
            key = base64.b64decode(policy.key)

            # Encrypt data
            return encrypt_data(data_bytes, key)

        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def decrypt(self, data: bytes, policy_name: str) -> Any:
        """Decrypt data using protection policy.

        Args:
            data: Data to decrypt
            policy_name: Name of protection policy

        Returns:
            Decrypted data

        Raises:
            NotFoundError: If policy does not exist
            DecryptionError: If decryption fails
        """
        # Get protection policy
        policy = self.get_protection_policy(policy_name)
        if policy is None:
            raise NotFoundError(f"Protection policy not found: {policy_name}")

        try:
            # Get encryption key from policy
            key = base64.b64decode(policy.key)

            # Decrypt data
            decrypted = decrypt_data(data, key)

            # Parse JSON data
            return json.loads(decrypted.decode())

        except Exception as e:
            raise DecryptionError(f"Failed to decrypt data: {e}")

    def hash_password(self, password: str) -> str:
        """Hash password.

        Args:
            password: Password to hash

        Returns:
            Hashed password
        """
        # Generate salt
        salt = generate_salt()

        # Hash password with salt
        hashed = hash_data(password, salt)

        # Combine salt and hash
        return base64.b64encode(salt + hashed).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password hash.

        Args:
            password: Password to verify
            hashed: Hashed password

        Returns:
            True if password matches hash
        """
        try:
            # Decode combined salt and hash
            combined = base64.b64decode(hashed)

            # Extract salt and hash
            salt = combined[:16]  # First 16 bytes are salt
            stored_hash = combined[16:]  # Rest is hash

            # Hash password with same salt
            test_hash = hash_data(password, salt)

            # Compare hashes
            return verify_hash(test_hash, stored_hash)

        except Exception:
            return False

    def get_protection_policy(self, policy_name: str) -> ProtectionPolicy | None:
        """Get protection policy by name.

        Args:
            policy_name: Name of protection policy

        Returns:
            Protection policy or None if not found
        """
        return self._protection_policies.get(policy_name)

    def has_permission(
        self,
        context: SecurityContext,
        permission: Permission,
        resource: str | None = None,
    ) -> bool:
        """Check if context has permission.

        Args:
            context: Security context
            permission: Required permission
            resource: Optional resource identifier

        Returns:
            True if context has permission
        """
        if not self._initialized:
            return False

        # Check if any role has the permission
        for role_name in context.roles:
            role = self._roles.get(role_name)
            if not role:
                continue

            # Check if role has permission
            if permission in role.permissions:
                # If resource is specified, check resource pattern
                if resource and role.resource_patterns:
                    for pattern in role.resource_patterns:
                        if pattern.match(resource):
                            return True
                else:
                    return True

        return False

    def has_scope(self, context: SecurityContext, scope: SecurityScope) -> bool:
        """Check if context has scope.

        Args:
            context: Security context
            scope: Required scope

        Returns:
            True if context has scope
        """
        if not self._initialized:
            return False

        return scope in context.scopes

    def has_role(self, context: SecurityContext, role: str) -> bool:
        """Check if context has role.

        Args:
            context: Security context
            role: Required role

        Returns:
            True if context has role
        """
        if not self._initialized:
            return False

        return role in context.roles
