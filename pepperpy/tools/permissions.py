"""Tool permissions system.

This module implements the permission management system for tools.
"""

from dataclasses import dataclass, field


@dataclass
class Permission:
    """Represents a tool permission."""

    name: str
    description: str
    parent: str | None = None


@dataclass
class PermissionSet:
    """Manages a set of permissions."""

    permissions: set[str] = field(default_factory=set)

    def add(self, permission: str) -> None:
        """Add a permission.

        Args:
            permission: Permission to add
        """
        self.permissions.add(permission)

    def remove(self, permission: str) -> None:
        """Remove a permission.

        Args:
            permission: Permission to remove
        """
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """Check if permission is present.

        Args:
            permission: Permission to check

        Returns:
            True if permission is present
        """
        return permission in self.permissions

    def has_any(self, permissions: set[str]) -> bool:
        """Check if any of the permissions are present.

        Args:
            permissions: Permissions to check

        Returns:
            True if any permission is present
        """
        return bool(self.permissions & permissions)

    def has_all(self, permissions: set[str]) -> bool:
        """Check if all permissions are present.

        Args:
            permissions: Permissions to check

        Returns:
            True if all permissions are present
        """
        return permissions <= self.permissions


class PermissionManager:
    """Manages tool permissions and inheritance."""

    def __init__(self) -> None:
        """Initialize the permission manager."""
        self._permissions: dict[str, Permission] = {}

    def register_permission(
        self, name: str, description: str, parent: str | None = None
    ) -> None:
        """Register a new permission.

        Args:
            name: Permission name
            description: Permission description
            parent: Optional parent permission
        """
        if parent and parent not in self._permissions:
            raise ValueError(f"Parent permission '{parent}' not found")

        self._permissions[name] = Permission(
            name=name,
            description=description,
            parent=parent,
        )

    def get_permission(self, name: str) -> Permission:
        """Get a permission by name.

        Args:
            name: Permission name

        Returns:
            Permission instance

        Raises:
            ValueError: If permission not found
        """
        if name not in self._permissions:
            raise ValueError(f"Permission '{name}' not found")
        return self._permissions[name]

    def get_effective_permissions(self, permission_set: PermissionSet) -> set[str]:
        """Get all effective permissions including inherited ones.

        Args:
            permission_set: Base permission set

        Returns:
            Set of all effective permissions
        """
        effective = set()
        for perm in permission_set.permissions:
            effective.add(perm)
            # Add parent permissions
            current = self._permissions.get(perm)
            while current and current.parent:
                effective.add(current.parent)
                current = self._permissions.get(current.parent)
        return effective
