"""Base interfaces for the security system.

Defines the interfaces and base classes for the security system,
including permissions, roles, and users.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Set
from uuid import UUID

from ..errors import PermissionError, SecurityError
from ..types import Result


class Permission:
    """Represents a permission that can be granted to principals."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class Principal(ABC):
    """Base class for security principals (users, roles, etc.)."""

    def __init__(self, name: str):
        self.name = name
        self.id = UUID()
        self._permissions: Set[Permission] = set()

    def add_permission(self, permission: Permission) -> None:
        """Add a permission to this principal."""
        self._permissions.add(permission)

    def remove_permission(self, permission: Permission) -> None:
        """Remove a permission from this principal."""
        self._permissions.discard(permission)

    def has_permission(self, permission: Permission) -> bool:
        """Check if this principal has a specific permission."""
        return permission in self._permissions

    def list_permissions(self) -> Set[Permission]:
        """List all permissions granted to this principal."""
        return self._permissions.copy()

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the principal.

        This method must be implemented by subclasses.
        """


class Role(Principal):
    """Represents a role that can be assigned to users."""



class User(Principal):
    """Represents a user in the system."""

    def __init__(self, name: str):
        super().__init__(name)
        self._roles: Set[Role] = set()

    def add_role(self, role: Role) -> None:
        """Add a role to this user."""
        self._roles.add(role)

    def remove_role(self, role: Role) -> None:
        """Remove a role from this user."""
        self._roles.discard(role)

    def has_role(self, role: Role) -> bool:
        """Check if this user has a specific role."""
        return role in self._roles

    def list_roles(self) -> Set[Role]:
        """List all roles assigned to this user."""
        return self._roles.copy()

    def has_permission(self, permission: Permission) -> bool:
        """Check if this user has a specific permission (directly or via roles)."""
        if super().has_permission(permission):
            return True
        return any(role.has_permission(permission) for role in self._roles)


class SecurityContext:
    """Represents the security context for an operation."""

    def __init__(self, user: Optional[User] = None):
        self.user = user
        self.required_permissions: Set[Permission] = set()

    def require_permission(self, permission: Permission) -> None:
        """Add a required permission to this context."""
        self.required_permissions.add(permission)

    def check_permissions(self) -> Result:
        """Check if all required permissions are satisfied."""
        if not self.user:
            return Result(success=False, error="No user in security context")

        missing = [
            p for p in self.required_permissions if not self.user.has_permission(p)
        ]

        if missing:
            return Result(
                success=False,
                error=f"Missing required permissions: {', '.join(p.name for p in missing)}",
            )

        return Result(success=True)


class SecurityManager:
    """Manager for security-related operations."""

    def __init__(self):
        self._users: Dict[UUID, User] = {}
        self._roles: Dict[UUID, Role] = {}
        self._permissions: Dict[str, Permission] = {}

    def create_permission(self, name: str, description: str = "") -> Permission:
        """Create a new permission."""
        if name in self._permissions:
            raise SecurityError(f"Permission {name} already exists")

        permission = Permission(name, description)
        self._permissions[name] = permission
        return permission

    def get_permission(self, name: str) -> Permission:
        """Get a permission by name."""
        if name not in self._permissions:
            raise SecurityError(f"Permission {name} not found")

        return self._permissions[name]

    def create_role(self, name: str) -> Role:
        """Create a new role."""
        role = Role(name)
        self._roles[role.id] = role
        return role

    def get_role(self, role_id: UUID) -> Role:
        """Get a role by ID."""
        if role_id not in self._roles:
            raise SecurityError(f"Role with ID {role_id} not found")

        return self._roles[role_id]

    def create_user(self, name: str) -> User:
        """Create a new user."""
        user = User(name)
        self._users[user.id] = user
        return user

    def get_user(self, user_id: UUID) -> User:
        """Get a user by ID."""
        if user_id not in self._users:
            raise SecurityError(f"User with ID {user_id} not found")

        return self._users[user_id]

    def check_permission(self, user: User, permission: Permission) -> None:
        """Check if a user has a specific permission."""
        if not user.has_permission(permission):
            raise PermissionError(
                f"User {user.name} does not have permission {permission.name}",
            )


def create_security_manager() -> SecurityManager:
    """Create and configure a new security manager instance."""
    return SecurityManager()


# Export all types
__all__ = [
    "Permission",
    "Principal",
    "Role",
    "SecurityContext",
    "SecurityManager",
    "User",
    "create_security_manager",
]
