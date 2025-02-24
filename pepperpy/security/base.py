"""Base security module for the Pepperpy framework.

This module provides core security functionality including:
- Authentication and authorization
- Encryption and data protection
- Security validation and verification
- Audit logging and monitoring
"""

import base64
import json
import re
from datetime import datetime, timedelta
from re import Pattern
from typing import Any
from uuid import UUID, uuid4

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import NotFoundError, ValidationError
from pepperpy.core.import_utils import import_optional_dependency
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.monitoring.audit import AuditLogger
from pepperpy.monitoring.metrics import MetricsManager
from pepperpy.security.errors import (
    AuthenticationError,
    DecryptionError,
    DuplicateError,
    EncryptionError,
    SecurityError,
)
from pepperpy.security.provider import SecurityProvider
from pepperpy.security.types import (
    ComponentConfig,
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

# Import pydantic safely
pydantic = import_optional_dependency("pydantic", "pydantic>=2.0.0")
if not pydantic:
    raise ImportError("pydantic is required for security types")


# Base security component
class SecurityComponent(Lifecycle):
    """Base class for security components.

    This class defines the core interface that all security components
    must implement, including lifecycle management and metrics.
    """

    def __init__(self, config: ComponentConfig) -> None:
        """Initialize security component.

        Args:
            config: Security configuration
        """
        super().__init__()
        self.config = config
        self._metrics = MetricsManager.get_instance()
        self._audit = AuditLogger()
        self._state = ComponentState.CREATED
        self._compiled_patterns: dict[str, Pattern[str]] = {}

    async def initialize(self) -> None:
        """Initialize component."""
        try:
            self._state = ComponentState.INITIALIZING
            await self._audit.log({
                "event_type": "security.component.initializing",
                "component": self.name,
                "type": self.type,
            })

            # Component-specific initialization
            await self._initialize_component()

            self._state = ComponentState.READY
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
            raise SecurityError(f"Failed to initialize {self.name}: {e}")

    async def cleanup(self) -> None:
        """Clean up component."""
        try:
            self._state = ComponentState.CLEANING
            await self._audit.log({
                "event_type": "security.component.cleaning",
                "component": self.name,
                "type": self.type,
            })

            # Component-specific cleanup
            await self._cleanup_component()

            self._state = ComponentState.CLEANED
            await self._audit.log({
                "event_type": "security.component.cleaned",
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
            raise SecurityError(f"Failed to clean up {self.name}: {e}")

    async def _initialize_component(self) -> None:
        """Initialize component implementation.

        This method should be overridden by subclasses to perform
        component-specific initialization.
        """
        pass

    async def _cleanup_component(self) -> None:
        """Clean up component implementation.

        This method should be overridden by subclasses to perform
        component-specific cleanup.
        """
        pass

    @property
    def id(self) -> str:
        """Get component ID."""
        return str(self.config.id)

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

    def get_metrics(self) -> dict[str, Any]:
        """Get component metrics.

        Returns:
            Dictionary containing component metrics
        """
        return {
            "state": self._state.value,
            "enabled": self.enabled,
        }

    def _compile_pattern(self, pattern: str) -> Pattern[str] | None:
        """Compile regex pattern.

        Args:
            pattern: Pattern string

        Returns:
            Compiled pattern or None if invalid
        """
        if pattern not in self._compiled_patterns:
            try:
                self._compiled_patterns[pattern] = re.compile(pattern)
            except re.error:
                logger.warning(
                    "Invalid resource pattern",
                    extra={
                        "pattern": pattern,
                        "component": self.name,
                    },
                )
                return None
        return self._compiled_patterns[pattern]


# Authentication component
class AuthenticationComponent(SecurityComponent):
    """Component for authentication.

    This component handles user authentication and token management.
    """

    def __init__(self, config: ComponentConfig) -> None:
        """Initialize authentication component.

        Args:
            config: Security configuration
        """
        super().__init__(config)
        self._tokens: dict[str, Token] = {}

    async def _initialize_component(self) -> None:
        """Initialize authentication component."""
        logger.info("Initializing authentication component")
        # Initialize token storage
        self._tokens = {}

    async def _cleanup_component(self) -> None:
        """Clean up authentication component."""
        logger.info("Cleaning up authentication component")
        # Clear token storage
        self._tokens.clear()

    async def authenticate(
        self,
        credentials: Credentials,
        scopes: set[SecurityScope] | None = None,
    ) -> Token:
        """Authenticate user and generate token.

        Args:
            credentials: User credentials
            scopes: Optional security scopes

        Returns:
            Authentication token

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Validate credentials
            if not credentials.user_id:
                raise AuthenticationError("Missing user ID")

            # Get token expiration from config
            token_expiration = self.config.config.get("token_expiration", 86400)

            # Generate token
            token = Token(
                token_id=uuid4(),
                user_id=credentials.user_id,
                scopes=scopes or set(),
                issued_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=token_expiration),
                metadata=credentials.metadata or {},
            )

            # Store token
            self._tokens[str(token.token_id)] = token

            return token

        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}")

    async def validate_token(self, token: Token) -> bool:
        """Validate token.

        Args:
            token: Token to validate

        Returns:
            True if token is valid
        """
        # Check if token exists
        stored_token = self._tokens.get(str(token.token_id))
        if not stored_token:
            return False

        # Check if token has expired
        if datetime.utcnow() > stored_token.expires_at:
            await self.revoke_token(token)
            return False

        return True

    async def refresh_token(self, token: Token) -> Token:
        """Refresh token.

        Args:
            token: Token to refresh

        Returns:
            New token

        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            # Validate existing token
            if not await self.validate_token(token):
                raise AuthenticationError("Invalid token")

            # Get token expiration from config
            token_expiration = self.config.config.get("token_expiration", 86400)

            # Generate new token
            new_token = Token(
                token_id=uuid4(),
                user_id=token.user_id,
                scopes=token.scopes,
                issued_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=token_expiration),
                metadata=token.metadata,
            )

            # Store new token
            self._tokens[str(new_token.token_id)] = new_token

            # Revoke old token
            await self.revoke_token(token)

            return new_token

        except Exception as e:
            raise AuthenticationError(f"Token refresh failed: {e}")

    async def revoke_token(self, token: Token) -> None:
        """Revoke token.

        Args:
            token: Token to revoke

        Raises:
            AuthenticationError: If token revocation fails
        """
        try:
            # Remove token from storage
            self._tokens.pop(str(token.token_id), None)

        except Exception as e:
            raise AuthenticationError(f"Token revocation failed: {e}")

    async def get_security_context(self, token: Token) -> SecurityContext:
        """Get security context from token.

        Args:
            token: Authentication token

        Returns:
            Security context

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Validate token
            if not await self.validate_token(token):
                raise AuthenticationError("Invalid token")

            # Create security context
            return SecurityContext(
                user_id=token.user_id,
                current_token=token,
                roles=set(),  # Roles should be populated by authorization component
                active_scopes=token.scopes,
                metadata=token.metadata,
            )

        except Exception as e:
            raise AuthenticationError(f"Failed to get security context: {e}")


# Authorization component
class AuthorizationComponent(SecurityComponent):
    """Component for authorization.

    This component handles role-based access control.
    """

    def __init__(self, config: ComponentConfig) -> None:
        """Initialize authorization component.

        Args:
            config: Security configuration
        """
        super().__init__(config)
        self._roles: dict[str, Role] = {}
        self._policies: dict[str, Policy] = {}

    async def _initialize_component(self) -> None:
        """Initialize authorization component."""
        logger.info("Initializing authorization component")
        # Initialize role and policy storage
        self._roles = {}
        self._policies = {}

    async def _cleanup_component(self) -> None:
        """Clean up authorization component."""
        logger.info("Cleaning up authorization component")
        # Clear role and policy storage
        self._roles.clear()
        self._policies.clear()

    async def authorize(
        self,
        context: SecurityContext,
        permission: Permission,
        resource: str | None = None,
    ) -> bool:
        """Authorize operation.

        Args:
            context: Security context
            permission: Required permission
            resource: Optional resource identifier

        Returns:
            True if authorized
        """
        # Check if context has required permission
        if not await self.has_permission(context, permission, resource):
            return False

        # Check if context has required scopes
        required_scopes = set()
        for role_name in context.roles:
            role = self._roles.get(role_name)
            if role and permission in role.permissions:
                # Get required scopes from policies
                for policy in self._policies.values():
                    if (
                        role_name in policy.roles
                        and permission in policy.actions
                        and (not resource or resource in policy.resources)
                    ):
                        required_scopes.update(policy.scopes)

        # Verify all required scopes are present
        for scope in required_scopes:
            if not await self.has_scope(context, scope):
                return False

        return True

    async def has_permission(
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
        # Check each role
        for role_name in context.roles:
            role = self._roles.get(role_name)
            if not role:
                continue

            # Check if role has permission
            if permission in role.permissions:
                # If resource is specified, check resource patterns
                if resource:
                    for pattern in role.resource_patterns:
                        compiled = self._compile_pattern(pattern)
                        if compiled and compiled.match(resource):
                            return True
                else:
                    return True

        return False

    async def has_scope(self, context: SecurityContext, scope: SecurityScope) -> bool:
        """Check if context has scope.

        Args:
            context: Security context
            scope: Required scope

        Returns:
            True if context has scope
        """
        return scope in context.active_scopes

    async def has_role(self, context: SecurityContext, role: str) -> bool:
        """Check if context has role.

        Args:
            context: Security context
            role: Required role

        Returns:
            True if context has role
        """
        return role in context.roles

    async def get_roles(self) -> list[Role]:
        """Get available roles.

        Returns:
            List of available roles
        """
        return list(self._roles.values())

    async def create_role(self, role: Role) -> Role:
        """Create role.

        Args:
            role: Role to create

        Returns:
            Created role

        Raises:
            ValidationError: If role is invalid
            DuplicateError: If role already exists
        """
        if role.name in self._roles:
            raise DuplicateError(f"Role already exists: {role.name}")

        self._roles[role.name] = role
        return role

    async def update_role(self, role: Role) -> Role:
        """Update role.

        Args:
            role: Role to update

        Returns:
            Updated role

        Raises:
            ValidationError: If role is invalid
            NotFoundError: If role does not exist
        """
        if role.name not in self._roles:
            raise NotFoundError(f"Role not found: {role.name}")

        self._roles[role.name] = role
        return role

    async def delete_role(self, role_name: str) -> None:
        """Delete role.

        Args:
            role_name: Role name

        Raises:
            NotFoundError: If role does not exist
        """
        if role_name not in self._roles:
            raise NotFoundError(f"Role not found: {role_name}")

        del self._roles[role_name]

    async def get_policies(self) -> list[Policy]:
        """Get security policies.

        Returns:
            List of policies
        """
        return list(self._policies.values())

    async def create_policy(self, policy: Policy) -> Policy:
        """Create policy.

        Args:
            policy: Policy to create

        Returns:
            Created policy

        Raises:
            ValidationError: If policy is invalid
            DuplicateError: If policy already exists
        """
        if policy.name in self._policies:
            raise DuplicateError(f"Policy already exists: {policy.name}")

        self._policies[policy.name] = policy
        return policy

    async def update_policy(self, policy: Policy) -> Policy:
        """Update policy.

        Args:
            policy: Policy to update

        Returns:
            Updated policy

        Raises:
            ValidationError: If policy is invalid
            NotFoundError: If policy does not exist
        """
        if policy.name not in self._policies:
            raise NotFoundError(f"Policy not found: {policy.name}")

        self._policies[policy.name] = policy
        return policy

    async def delete_policy(self, policy_name: str) -> None:
        """Delete policy.

        Args:
            policy_name: Policy name

        Raises:
            NotFoundError: If policy does not exist
        """
        if policy_name not in self._policies:
            raise NotFoundError(f"Policy not found: {policy_name}")

        del self._policies[policy_name]


# Data protection component
class DataProtectionComponent(SecurityComponent):
    """Component for data protection.

    This component handles data encryption and masking.
    """

    def __init__(self, config: ComponentConfig) -> None:
        """Initialize data protection component.

        Args:
            config: Security configuration
        """
        super().__init__(config)
        self._protection_policies: dict[str, ProtectionPolicy] = {}

    async def _initialize_component(self) -> None:
        """Initialize data protection component."""
        logger.info("Initializing data protection component")
        # Initialize protection policy storage
        self._protection_policies = {}

    async def _cleanup_component(self) -> None:
        """Clean up data protection component."""
        logger.info("Cleaning up data protection component")
        # Clear protection policy storage
        self._protection_policies.clear()

    async def get_protection_policies(self) -> list[ProtectionPolicy]:
        """Get data protection policies.

        Returns:
            List of protection policies
        """
        return list(self._protection_policies.values())

    async def create_protection_policy(
        self, policy: ProtectionPolicy
    ) -> ProtectionPolicy:
        """Create data protection policy.

        Args:
            policy: Policy to create

        Returns:
            Created policy

        Raises:
            ValidationError: If policy is invalid
            DuplicateError: If policy already exists
        """
        if policy.name in self._protection_policies:
            raise DuplicateError(f"Protection policy already exists: {policy.name}")

        self._protection_policies[policy.name] = policy
        return policy

    async def update_protection_policy(
        self, policy: ProtectionPolicy
    ) -> ProtectionPolicy:
        """Update data protection policy.

        Args:
            policy: Policy to update

        Returns:
            Updated policy

        Raises:
            ValidationError: If policy is invalid
            NotFoundError: If policy does not exist
        """
        if policy.name not in self._protection_policies:
            raise NotFoundError(f"Protection policy not found: {policy.name}")

        self._protection_policies[policy.name] = policy
        return policy

    async def delete_protection_policy(self, policy_name: str) -> None:
        """Delete data protection policy.

        Args:
            policy_name: Name of policy to delete

        Raises:
            NotFoundError: If policy does not exist
        """
        if policy_name not in self._protection_policies:
            raise NotFoundError(f"Protection policy not found: {policy_name}")

        del self._protection_policies[policy_name]

    async def encrypt(self, data: Any, policy_name: str) -> bytes:
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
        policy = self._protection_policies.get(policy_name)
        if policy is None:
            raise NotFoundError(f"Protection policy not found: {policy_name}")

        try:
            # Serialize data to JSON
            data_json = json.dumps(data)
            data_bytes = data_json.encode()

            # Get encryption key from policy
            if not policy.encryption_key_id:
                raise EncryptionError("Encryption key not configured")

            # Get key from key manager
            key = await self._get_encryption_key(policy.encryption_key_id)

            # Encrypt data
            return encrypt_data(data_bytes, key)

        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {e}")

    async def decrypt(self, data: bytes, policy_name: str) -> Any:
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
        policy = self._protection_policies.get(policy_name)
        if policy is None:
            raise NotFoundError(f"Protection policy not found: {policy_name}")

        try:
            # Get encryption key from policy
            if not policy.encryption_key_id:
                raise DecryptionError("Encryption key not configured")

            # Get key from key manager
            key = await self._get_encryption_key(policy.encryption_key_id)

            # Decrypt data
            decrypted = decrypt_data(data, key)

            # Parse JSON data
            return json.loads(decrypted.decode())

        except Exception as e:
            raise DecryptionError(f"Failed to decrypt data: {e}")

    async def _get_encryption_key(self, key_id: str) -> bytes:
        """Get encryption key from key manager.

        Args:
            key_id: Key identifier

        Returns:
            Encryption key

        Raises:
            EncryptionError: If key retrieval fails
        """
        # TODO: Implement key management
        # For now, return a dummy key
        return b"dummy_key_for_testing_only"


# Export public API
__all__ = [
    "AuthenticationComponent",
    "AuthorizationComponent",
    "DataProtectionComponent",
    "SecurityComponent",
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
        self._compiled_patterns: dict[str, Pattern[str]] = {}

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
        self._config = SecurityConfig()  # Reset to default config instead of None
        self._roles.clear()
        self._policies.clear()
        self._protection_policies.clear()
        self._tokens.clear()
        self._security_contexts.clear()
        self._compiled_patterns.clear()

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

        Raises:
            ValidationError: If provider not initialized
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        # Always return a valid SecurityConfig
        return self._config

    def update_config(self, config: SecurityConfig) -> SecurityConfig:
        """Update security configuration.

        Args:
            config: New security configuration

        Returns:
            Updated security configuration

        Raises:
            ValidationError: If provider not initialized
        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

        # Update configuration
        self._config = config
        return self._config

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
                        compiled = self._compile_pattern(pattern)
                        if compiled and compiled.match(resource):
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

        return scope in context.active_scopes

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

    def _compile_pattern(self, pattern: str) -> Pattern[str] | None:
        """Compile regex pattern.

        Args:
            pattern: Pattern string

        Returns:
            Compiled pattern or None if invalid
        """
        if pattern not in self._compiled_patterns:
            try:
                self._compiled_patterns[pattern] = re.compile(pattern)
            except re.error:
                logger.warning(
                    "Invalid resource pattern",
                    extra={
                        "pattern": pattern,
                        "component": self.get_name(),
                    },
                )
                return None
        return self._compiled_patterns[pattern]
