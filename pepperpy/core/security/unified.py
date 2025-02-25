"""Unified security system for Pepperpy.

This module provides a comprehensive security framework that includes:
- Authentication and authorization
- Data protection and encryption
- Security policy management
- Audit logging and monitoring
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Generic, TypeVar

from pepperpy.core.errors.unified import PepperpyError
from pepperpy.core.metrics.unified import MetricsManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SecurityError(PepperpyError):
    """Base class for security-related errors."""

    def __init__(self, message: str, code: str = "SEC001", **kwargs: Any) -> None:
        """Initialize the error."""
        super().__init__(message, code=code, category="security", **kwargs)


class SecurityLevel(Enum):
    """Security levels for operations and data."""

    LOW = "low"  # Basic security, public data
    MEDIUM = "medium"  # Enhanced security, internal data
    HIGH = "high"  # Maximum security, sensitive data


@dataclass
class SecurityContext:
    """Security context for operations."""

    user_id: str
    roles: list[str]
    permissions: list[str]
    level: SecurityLevel
    metadata: dict[str, Any]
    created_at: datetime = datetime.now()
    expires_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "user_id": self.user_id,
            "roles": self.roles,
            "permissions": self.permissions,
            "level": self.level.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def is_expired(self) -> bool:
        """Check if context has expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    def has_permission(self, permission: str) -> bool:
        """Check if context has specific permission."""
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        """Check if context has specific role."""
        return role in self.roles


class SecurityProvider(ABC, Generic[T]):
    """Base class for security providers."""

    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> SecurityContext:
        """Authenticate user and create security context.

        Args:
            credentials: Authentication credentials.

        Returns:
            Security context for authenticated user.

        Raises:
            SecurityError: If authentication fails.
        """
        pass

    @abstractmethod
    async def authorize(
        self, context: SecurityContext, resource: str, action: str
    ) -> bool:
        """Check if context is authorized for action on resource.

        Args:
            context: Security context.
            resource: Resource to access.
            action: Action to perform.

        Returns:
            True if authorized, False otherwise.
        """
        pass

    @abstractmethod
    async def validate(self, context: SecurityContext) -> list[str]:
        """Validate security context.

        Args:
            context: Security context to validate.

        Returns:
            List of validation errors.
        """
        pass

    @abstractmethod
    async def encrypt(self, data: T, context: SecurityContext) -> bytes:
        """Encrypt data using context's security level.

        Args:
            data: Data to encrypt.
            context: Security context.

        Returns:
            Encrypted data.

        Raises:
            SecurityError: If encryption fails.
        """
        pass

    @abstractmethod
    async def decrypt(self, data: bytes, context: SecurityContext) -> T:
        """Decrypt data using context's security level.

        Args:
            data: Data to decrypt.
            context: Security context.

        Returns:
            Decrypted data.

        Raises:
            SecurityError: If decryption fails.
        """
        pass


class BaseSecurityProvider(SecurityProvider[T]):
    """Base implementation of security provider."""

    def __init__(self) -> None:
        """Initialize the base security provider."""
        self._metrics = MetricsManager.get_instance()
        self._lock = asyncio.Lock()

    async def authenticate(self, credentials: dict[str, Any]) -> SecurityContext:
        """Authenticate user and create security context."""
        try:
            user_id = await self._validate_credentials(credentials)
            roles = await self._get_user_roles(user_id)
            permissions = await self._get_role_permissions(roles)

            context = SecurityContext(
                user_id=user_id,
                roles=roles,
                permissions=permissions,
                level=SecurityLevel.MEDIUM,
                metadata={"auth_method": credentials.get("method", "default")},
                expires_at=datetime.now() + timedelta(hours=1),
            )

            await self._record_operation("authenticate", True)
            return context

        except Exception as e:
            await self._record_operation("authenticate", False)
            raise SecurityError(f"Authentication failed: {e}", code="SEC002") from e

    async def authorize(
        self, context: SecurityContext, resource: str, action: str
    ) -> bool:
        """Check if context is authorized for action on resource."""
        if context.is_expired():
            await self._record_operation(
                "authorize", False, reason="expired", resource=resource
            )
            return False

        # Check direct permission
        permission = f"{resource}:{action}"
        if context.has_permission(permission):
            await self._record_operation(
                "authorize", True, resource=resource, action=action
            )
            return True

        # Check role-based permissions
        for role in context.roles:
            if await self._check_role_permission(role, resource, action):
                await self._record_operation(
                    "authorize",
                    True,
                    resource=resource,
                    action=action,
                    role=role,
                )
                return True

        await self._record_operation(
            "authorize",
            False,
            reason="unauthorized",
            resource=resource,
            action=action,
        )
        return False

    async def validate(self, context: SecurityContext) -> list[str]:
        """Validate security context."""
        errors = []

        if not context.user_id:
            errors.append("Missing user ID")

        if not context.roles:
            errors.append("No roles assigned")

        if context.is_expired():
            errors.append("Context has expired")

        if context.level not in SecurityLevel:
            errors.append("Invalid security level")

        return errors

    async def encrypt(self, data: T, context: SecurityContext) -> bytes:
        """Encrypt data using context's security level."""
        try:
            if context.is_expired():
                raise SecurityError("Cannot encrypt with expired context")

            encrypted = await self._encrypt_data(data, context.level)
            await self._record_operation(
                "encrypt",
                True,
                level=context.level.value,
            )
            return encrypted

        except Exception as e:
            await self._record_operation(
                "encrypt",
                False,
                level=context.level.value,
            )
            raise SecurityError(f"Encryption failed: {e}", code="SEC003") from e

    async def decrypt(self, data: bytes, context: SecurityContext) -> T:
        """Decrypt data using context's security level."""
        try:
            if context.is_expired():
                raise SecurityError("Cannot decrypt with expired context")

            decrypted = await self._decrypt_data(data, context.level)
            await self._record_operation(
                "decrypt",
                True,
                level=context.level.value,
            )
            return decrypted

        except Exception as e:
            await self._record_operation(
                "decrypt",
                False,
                level=context.level.value,
            )
            raise SecurityError(f"Decryption failed: {e}", code="SEC004") from e

    async def _validate_credentials(self, credentials: dict[str, Any]) -> str:
        """Validate credentials and return user ID."""
        # Implement credential validation
        return "test_user"

    async def _get_user_roles(self, user_id: str) -> list[str]:
        """Get roles for user."""
        # Implement role lookup
        return ["user"]

    async def _get_role_permissions(self, roles: list[str]) -> list[str]:
        """Get permissions for roles."""
        # Implement permission lookup
        return ["resource:read"]

    async def _check_role_permission(
        self, role: str, resource: str, action: str
    ) -> bool:
        """Check if role has permission for action on resource."""
        # Implement permission check
        return False

    async def _encrypt_data(self, data: T, level: SecurityLevel) -> bytes:
        """Encrypt data with security level."""
        # Implement encryption
        return b""

    async def _decrypt_data(self, data: bytes, level: SecurityLevel) -> T:
        """Decrypt data with security level."""
        # Implement decryption
        return None  # type: ignore

    async def _record_operation(
        self, operation: str, success: bool = True, **labels: str
    ) -> None:
        """Record security operation metric."""
        self._metrics.counter(
            f"security_provider_{operation}",
            1,
            success=str(success).lower(),
            **labels,
        )


class SecurityManager:
    """Manager for security operations."""

    def __init__(self) -> None:
        """Initialize the security manager."""
        self._providers: dict[str, SecurityProvider] = {}
        self._metrics = MetricsManager.get_instance()
        self._lock = asyncio.Lock()

    def register_provider(
        self, name: str, provider: SecurityProvider, default: bool = False
    ) -> None:
        """Register a security provider.

        Args:
            name: Provider name.
            provider: Provider instance.
            default: Whether this is the default provider.

        Raises:
            SecurityError: If provider already exists.
        """
        if name in self._providers:
            raise SecurityError(
                f"Provider already exists: {name}",
                code="SEC005",
            )

        self._providers[name] = provider
        if default:
            self._providers["default"] = provider

        self._metrics.counter(
            "security_provider_registered",
            1,
            provider=name,
            default=str(default).lower(),
        )

    async def authenticate(
        self,
        credentials: dict[str, Any],
        provider: str | None = None,
    ) -> SecurityContext:
        """Authenticate using provider.

        Args:
            credentials: Authentication credentials.
            provider: Optional provider name.

        Returns:
            Security context.

        Raises:
            SecurityError: If authentication fails.
        """
        provider_name = provider or "default"
        if provider_name not in self._providers:
            raise SecurityError(
                f"Provider not found: {provider_name}",
                code="SEC006",
            )

        return await self._providers[provider_name].authenticate(credentials)

    async def authorize(
        self,
        context: SecurityContext,
        resource: str,
        action: str,
        provider: str | None = None,
    ) -> bool:
        """Check authorization using provider.

        Args:
            context: Security context.
            resource: Resource to access.
            action: Action to perform.
            provider: Optional provider name.

        Returns:
            True if authorized, False otherwise.

        Raises:
            SecurityError: If provider not found.
        """
        provider_name = provider or "default"
        if provider_name not in self._providers:
            raise SecurityError(
                f"Provider not found: {provider_name}",
                code="SEC007",
            )

        return await self._providers[provider_name].authorize(context, resource, action)

    async def encrypt(
        self,
        data: Any,
        context: SecurityContext,
        provider: str | None = None,
    ) -> bytes:
        """Encrypt data using provider.

        Args:
            data: Data to encrypt.
            context: Security context.
            provider: Optional provider name.

        Returns:
            Encrypted data.

        Raises:
            SecurityError: If encryption fails.
        """
        provider_name = provider or "default"
        if provider_name not in self._providers:
            raise SecurityError(
                f"Provider not found: {provider_name}",
                code="SEC008",
            )

        return await self._providers[provider_name].encrypt(data, context)

    async def decrypt(
        self,
        data: bytes,
        context: SecurityContext,
        provider: str | None = None,
    ) -> Any:
        """Decrypt data using provider.

        Args:
            data: Data to decrypt.
            context: Security context.
            provider: Optional provider name.

        Returns:
            Decrypted data.

        Raises:
            SecurityError: If decryption fails.
        """
        provider_name = provider or "default"
        if provider_name not in self._providers:
            raise SecurityError(
                f"Provider not found: {provider_name}",
                code="SEC009",
            )

        return await self._providers[provider_name].decrypt(data, context)


class SecurityMonitor:
    """Monitor for security operations."""

    def __init__(self) -> None:
        """Initialize the security monitor."""
        self._metrics = MetricsManager.get_instance()

    async def record_event(
        self,
        event_type: str,
        context: SecurityContext | None = None,
        success: bool = True,
        **labels: str,
    ) -> None:
        """Record security event.

        Args:
            event_type: Type of security event.
            context: Optional security context.
            success: Whether event was successful.
            **labels: Additional metric labels.
        """
        event_labels = {
            "event_type": event_type,
            "success": str(success).lower(),
        }

        if context:
            event_labels.update({
                "user_id": context.user_id,
                "level": context.level.value,
            })

        event_labels.update(labels)

        self._metrics.counter("security_events", 1, **event_labels)

        if not success:
            logger.warning(
                "Security event failed",
                extra={
                    "event_type": event_type,
                    "context": context.to_dict() if context else None,
                    **labels,
                },
            )
