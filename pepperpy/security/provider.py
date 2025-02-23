"""Security provider interface.

This module defines the contract for security implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Set

from pepperpy.core.provider import Provider
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


class SecurityProvider(Provider, ABC):
    """Security provider interface."""

    @abstractmethod
    def authenticate(
        self,
        credentials: Credentials,
        scopes: Optional[Set[SecurityScope]] = None,
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
        raise NotImplementedError

    @abstractmethod
    def validate_token(self, token: Token) -> bool:
        """Validate token.

        Args:
            token: Token to validate

        Returns:
            True if token is valid
        """
        raise NotImplementedError

    @abstractmethod
    def refresh_token(self, token: Token) -> Token:
        """Refresh token.

        Args:
            token: Token to refresh

        Returns:
            New token

        Raises:
            AuthenticationError: If token refresh fails
        """
        raise NotImplementedError

    @abstractmethod
    def revoke_token(self, token: Token) -> None:
        """Revoke token.

        Args:
            token: Token to revoke

        Raises:
            AuthenticationError: If token revocation fails
        """
        raise NotImplementedError

    @abstractmethod
    def get_security_context(self, token: Token) -> SecurityContext:
        """Get security context from token.

        Args:
            token: Authentication token

        Returns:
            Security context

        Raises:
            AuthenticationError: If token is invalid
        """
        raise NotImplementedError

    @abstractmethod
    def has_permission(
        self,
        context: SecurityContext,
        permission: Permission,
        resource: Optional[str] = None,
    ) -> bool:
        """Check if context has permission.

        Args:
            context: Security context
            permission: Required permission
            resource: Optional resource identifier

        Returns:
            True if context has permission
        """
        raise NotImplementedError

    @abstractmethod
    def has_scope(self, context: SecurityContext, scope: SecurityScope) -> bool:
        """Check if context has scope.

        Args:
            context: Security context
            scope: Required scope

        Returns:
            True if context has scope
        """
        raise NotImplementedError

    @abstractmethod
    def has_role(self, context: SecurityContext, role: str) -> bool:
        """Check if context has role.

        Args:
            context: Security context
            role: Required role

        Returns:
            True if context has role
        """
        raise NotImplementedError

    @abstractmethod
    def get_roles(self) -> List[Role]:
        """Get available roles.

        Returns:
            List of available roles
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def delete_role(self, role_name: str) -> None:
        """Delete role.

        Args:
            role_name: Name of role to delete

        Raises:
            NotFoundError: If role does not exist
        """
        raise NotImplementedError

    @abstractmethod
    def get_policies(self) -> List[Policy]:
        """Get security policies.

        Returns:
            List of security policies
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def delete_policy(self, policy_name: str) -> None:
        """Delete security policy.

        Args:
            policy_name: Name of policy to delete

        Raises:
            NotFoundError: If policy does not exist
        """
        raise NotImplementedError

    @abstractmethod
    def get_protection_policies(self) -> List[ProtectionPolicy]:
        """Get data protection policies.

        Returns:
            List of protection policies
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def delete_protection_policy(self, policy_name: str) -> None:
        """Delete data protection policy.

        Args:
            policy_name: Name of policy to delete

        Raises:
            NotFoundError: If policy does not exist
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash password.

        Args:
            password: Password to hash

        Returns:
            Hashed password
        """
        raise NotImplementedError

    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password hash.

        Args:
            password: Password to verify
            hashed: Hashed password

        Returns:
            True if password matches hash
        """
        raise NotImplementedError

    @abstractmethod
    def get_config(self) -> SecurityConfig:
        """Get security configuration.

        Returns:
            Security configuration
        """
        raise NotImplementedError

    @abstractmethod
    def update_config(self, config: SecurityConfig) -> SecurityConfig:
        """Update security configuration.

        Args:
            config: New configuration

        Returns:
            Updated configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        raise NotImplementedError
