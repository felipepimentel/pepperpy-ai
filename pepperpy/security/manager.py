"""Security manager for the Pepperpy framework.

This module provides the security manager that handles security component
registration, lifecycle management, and security operations.
"""

from typing import Any, TypeVar

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.monitoring.audit import AuditLogger
from pepperpy.monitoring.metrics import MetricsManager
from pepperpy.security.base import (
    AuthenticationComponent,
    AuthorizationComponent,
    DataProtectionComponent,
    SecurityComponent,
)
from pepperpy.security.errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    SecurityError,
)
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

# Configure logging
logger = logger.getChild(__name__)

# Type variables
T = TypeVar("T", bound=SecurityComponent)


class SecurityManager(Lifecycle):
    """Manager for security components.

    This class manages security component registration, initialization,
    and operations for the framework.
    """

    def __init__(self, config: SecurityConfig | None = None) -> None:
        """Initialize security manager.

        Args:
            config: Optional security configuration
        """
        super().__init__()
        self._config = config or SecurityConfig()
        self._components: dict[str, SecurityComponent] = {}
        self._metrics = MetricsManager.get_instance()
        self._audit = AuditLogger()
        self._state = ComponentState.CREATED

        # Initialize core components with component configs
        self._auth = AuthenticationComponent(
            ComponentConfig(
                name="authentication",
                type="auth",
                config={"token_expiration": self._config.token_expiration},
            )
        )
        self._authz = AuthorizationComponent(
            ComponentConfig(
                name="authorization",
                type="authz",
                config={},
            )
        )
        self._protection = DataProtectionComponent(
            ComponentConfig(
                name="protection",
                type="protection",
                config={"encryption_algorithm": self._config.encryption_algorithm},
            )
        )

        # Register core components
        self.register_component(self._auth)
        self.register_component(self._authz)
        self.register_component(self._protection)

    async def _initialize(self) -> None:
        """Initialize security manager."""
        try:
            self._state = ComponentState.INITIALIZING

            # Initialize all components
            for component in self._components.values():
                await component.initialize()

            self._state = ComponentState.READY
            logger.info("Security manager initialized")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error("Failed to initialize security manager", exc_info=True)
            raise SecurityError(f"Failed to initialize security manager: {e}")

    async def _cleanup(self) -> None:
        """Clean up security manager."""
        try:
            self._state = ComponentState.CLEANING

            # Clean up all components
            for component in self._components.values():
                await component.cleanup()

            self._state = ComponentState.CLEANED
            logger.info("Security manager cleaned up")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error("Failed to clean up security manager", exc_info=True)
            raise SecurityError(f"Failed to clean up security manager: {e}")

    def register_component(self, component: SecurityComponent) -> None:
        """Register security component.

        Args:
            component: Security component to register

        Raises:
            ConfigurationError: If component is already registered
        """
        if component.name in self._components:
            raise ConfigurationError(f"Component already registered: {component.name}")

        self._components[component.name] = component
        logger.info(f"Registered security component: {component.name}")

    def unregister_component(self, name: str) -> None:
        """Unregister security component.

        Args:
            name: Component name

        Raises:
            ConfigurationError: If component is not registered
        """
        if name not in self._components:
            raise ConfigurationError(f"Component not registered: {name}")

        del self._components[name]
        logger.info(f"Unregistered security component: {name}")

    def get_component(self, name: str) -> SecurityComponent | None:
        """Get security component.

        Args:
            name: Component name

        Returns:
            Security component or None if not found
        """
        return self._components.get(name)

    def get_components(self) -> list[SecurityComponent]:
        """Get all security components.

        Returns:
            List of security components
        """
        return list(self._components.values())

    def get_component_by_type(self, component_type: type[T]) -> T | None:
        """Get component by type.

        Args:
            component_type: Component type

        Returns:
            Component instance or None if not found
        """
        for component in self._components.values():
            if isinstance(component, component_type):
                return component
        return None

    async def authenticate(
        self,
        credentials: Credentials,
        scopes: set[SecurityScope] | None = None,
    ) -> Token:
        """Authenticate user.

        Args:
            credentials: User credentials
            scopes: Optional security scopes

        Returns:
            Authentication token

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            return await self._auth.authenticate(credentials, scopes)
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}")

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

        Raises:
            AuthorizationError: If authorization fails
        """
        try:
            return await self._authz.authorize(context, permission, resource)
        except Exception as e:
            raise AuthorizationError(f"Authorization failed: {e}")

    async def validate_token(self, token: Token) -> bool:
        """Validate token.

        Args:
            token: Token to validate

        Returns:
            True if token is valid
        """
        return await self._auth.validate_token(token)

    async def refresh_token(self, token: Token) -> Token:
        """Refresh token.

        Args:
            token: Token to refresh

        Returns:
            New token

        Raises:
            AuthenticationError: If token refresh fails
        """
        return await self._auth.refresh_token(token)

    async def revoke_token(self, token: Token) -> None:
        """Revoke token.

        Args:
            token: Token to revoke

        Raises:
            AuthenticationError: If token revocation fails
        """
        await self._auth.revoke_token(token)

    async def get_security_context(self, token: Token) -> SecurityContext:
        """Get security context.

        Args:
            token: Authentication token

        Returns:
            Security context

        Raises:
            AuthenticationError: If token is invalid
        """
        return await self._auth.get_security_context(token)

    async def encrypt(self, data: Any, policy_name: str) -> bytes:
        """Encrypt data.

        Args:
            data: Data to encrypt
            policy_name: Protection policy name

        Returns:
            Encrypted data

        Raises:
            SecurityError: If encryption fails
        """
        return await self._protection.encrypt(data, policy_name)

    async def decrypt(self, data: bytes, policy_name: str) -> Any:
        """Decrypt data.

        Args:
            data: Data to decrypt
            policy_name: Protection policy name

        Returns:
            Decrypted data

        Raises:
            SecurityError: If decryption fails
        """
        return await self._protection.decrypt(data, policy_name)

    async def get_roles(self) -> list[Role]:
        """Get available roles.

        Returns:
            List of roles
        """
        return await self._authz.get_roles()

    async def create_role(self, role: Role) -> Role:
        """Create role.

        Args:
            role: Role to create

        Returns:
            Created role

        Raises:
            SecurityError: If role creation fails
        """
        return await self._authz.create_role(role)

    async def update_role(self, role: Role) -> Role:
        """Update role.

        Args:
            role: Role to update

        Returns:
            Updated role

        Raises:
            SecurityError: If role update fails
        """
        return await self._authz.update_role(role)

    async def delete_role(self, role_name: str) -> None:
        """Delete role.

        Args:
            role_name: Role name

        Raises:
            SecurityError: If role deletion fails
        """
        await self._authz.delete_role(role_name)

    async def get_policies(self) -> list[Policy]:
        """Get security policies.

        Returns:
            List of policies
        """
        return await self._authz.get_policies()

    async def create_policy(self, policy: Policy) -> Policy:
        """Create policy.

        Args:
            policy: Policy to create

        Returns:
            Created policy

        Raises:
            SecurityError: If policy creation fails
        """
        return await self._authz.create_policy(policy)

    async def update_policy(self, policy: Policy) -> Policy:
        """Update policy.

        Args:
            policy: Policy to update

        Returns:
            Updated policy

        Raises:
            SecurityError: If policy update fails
        """
        return await self._authz.update_policy(policy)

    async def delete_policy(self, policy_name: str) -> None:
        """Delete policy.

        Args:
            policy_name: Policy name

        Raises:
            SecurityError: If policy deletion fails
        """
        await self._authz.delete_policy(policy_name)

    async def get_protection_policies(self) -> list[ProtectionPolicy]:
        """Get protection policies.

        Returns:
            List of protection policies
        """
        return await self._protection.get_protection_policies()

    async def create_protection_policy(
        self, policy: ProtectionPolicy
    ) -> ProtectionPolicy:
        """Create protection policy.

        Args:
            policy: Policy to create

        Returns:
            Created policy

        Raises:
            SecurityError: If policy creation fails
        """
        return await self._protection.create_protection_policy(policy)

    async def update_protection_policy(
        self, policy: ProtectionPolicy
    ) -> ProtectionPolicy:
        """Update protection policy.

        Args:
            policy: Policy to update

        Returns:
            Updated policy

        Raises:
            SecurityError: If policy update fails
        """
        return await self._protection.update_protection_policy(policy)

    async def delete_protection_policy(self, policy_name: str) -> None:
        """Delete protection policy.

        Args:
            policy_name: Policy name

        Raises:
            SecurityError: If policy deletion fails
        """
        await self._protection.delete_protection_policy(policy_name)

    def get_config(self) -> SecurityConfig:
        """Get security configuration.

        Returns:
            Security configuration
        """
        return self._config

    def update_config(self, config: SecurityConfig) -> SecurityConfig:
        """Update security configuration.

        Args:
            config: New configuration

        Returns:
            Updated configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            self._config = config
            for component in self._components.values():
                component.config = config
            return self._config
        except Exception as e:
            raise ConfigurationError(f"Failed to update configuration: {e}")

    def get_metrics(self) -> dict[str, Any]:
        """Get security metrics.

        Returns:
            Dictionary containing metrics from all components
        """
        metrics = {}
        for component in self._components.values():
            metrics[component.name] = component.get_metrics()
        return metrics

    def get_status(self) -> dict[str, Any]:
        """Get security status.

        Returns:
            Dictionary containing status from all components
        """
        return {
            "state": self._state.value,
            "components": {
                name: component._state.value
                for name, component in self._components.items()
            },
            "metrics": self.get_metrics(),
        }


# Export public API
__all__ = [
    "SecurityManager",
]
