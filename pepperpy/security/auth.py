"""Authentication and authorization functionality.

This module provides classes for managing authentication and authorization:
1. AuthenticationManager - Handles user authentication and session management
2. AuthorizationManager - Handles permission checking and role-based access control
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from pepperpy.core.common.base import BaseManager
from pepperpy.core.common.types import UserId


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""

    pass


@dataclass
class Session:
    """Represents an authenticated user session."""

    user_id: UserId
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    scopes: set[str] = field(default_factory=set)
    metadata: dict[str, str] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return bool(self.expires_at and datetime.utcnow() > self.expires_at)


class AuthenticationManager(BaseManager):
    """Manages user authentication and sessions."""

    def __init__(self, session_timeout: timedelta = timedelta(hours=1)):
        """Initialize the authentication manager.

        Args:
            session_timeout: How long sessions should last before expiring
        """
        self._sessions: dict[str, Session] = {}
        self._session_timeout = session_timeout

    def authenticate(self, user_id: UserId, scopes: set[str] | None = None) -> str:
        """Authenticate a user and create a new session.

        Args:
            user_id: The ID of the user to authenticate
            scopes: Optional set of scopes to grant to the session

        Returns:
            The session token

        Raises:
            AuthenticationError: If authentication fails
        """
        session = Session(
            user_id=user_id,
            scopes=scopes or set(),
            expires_at=datetime.utcnow() + self._session_timeout,
        )
        token = self._generate_token()
        self._sessions[token] = session
        return token

    def validate_session(self, token: str) -> Session:
        """Validate a session token and return the associated session.

        Args:
            token: The session token to validate

        Returns:
            The associated session if valid

        Raises:
            AuthenticationError: If the token is invalid or expired
        """
        try:
            session = self._sessions[token]
        except KeyError:
            raise AuthenticationError("Invalid session token")

        if session.is_expired():
            del self._sessions[token]
            raise AuthenticationError("Session expired")

        return session

    def revoke_session(self, token: str) -> None:
        """Revoke a session token.

        Args:
            token: The session token to revoke
        """
        self._sessions.pop(token, None)

    def _generate_token(self) -> str:
        """Generate a unique session token."""
        # TODO: Implement secure token generation
        return "dummy_token"


class AuthorizationManager(BaseManager):
    """Manages authorization and access control."""

    def __init__(self):
        """Initialize the authorization manager."""
        self._role_permissions: dict[str, set[str]] = {}
        self._user_roles: dict[UserId, set[str]] = {}

    def add_role(self, role: str, permissions: set[str]) -> None:
        """Add or update a role with its permissions.

        Args:
            role: The role name
            permissions: Set of permissions granted by the role
        """
        self._role_permissions[role] = permissions

    def assign_role(self, user_id: UserId, role: str) -> None:
        """Assign a role to a user.

        Args:
            user_id: The user to assign the role to
            role: The role to assign

        Raises:
            AuthorizationError: If the role doesn't exist
        """
        if role not in self._role_permissions:
            raise AuthorizationError(f"Role {role} does not exist")

        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        self._user_roles[user_id].add(role)

    def check_permission(self, user_id: UserId, permission: str) -> bool:
        """Check if a user has a specific permission.

        Args:
            user_id: The user to check permissions for
            permission: The permission to check

        Returns:
            True if the user has the permission, False otherwise
        """
        user_roles = self._user_roles.get(user_id, set())
        for role in user_roles:
            if permission in self._role_permissions[role]:
                return True
        return False

    def get_user_permissions(self, user_id: UserId) -> set[str]:
        """Get all permissions granted to a user through their roles.

        Args:
            user_id: The user to get permissions for

        Returns:
            Set of all permissions granted to the user
        """
        permissions = set()
        user_roles = self._user_roles.get(user_id, set())
        for role in user_roles:
            permissions.update(self._role_permissions[role])
        return permissions
