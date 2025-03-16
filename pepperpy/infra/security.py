"""Core abstractions and implementations for security.

This module provides the core abstractions and implementations for security
in the PepperPy framework, including authentication, authorization, encryption,
and other security-related functionality.
"""

import datetime
import secrets
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AuthType(Enum):
    """Types of authentication."""

    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    JWT = "jwt"
    BASIC = "basic"
    CUSTOM = "custom"


class PermissionLevel(Enum):
    """Permission levels for authorization."""

    NONE = 0
    READ = 10
    WRITE = 20
    ADMIN = 30
    SYSTEM = 40


@dataclass
class Credential:
    """A credential for authentication.

    A credential represents a piece of information that can be used for
    authentication, such as an API key, username/password, or token.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    auth_type: AuthType = AuthType.NONE
    key: str = ""
    secret: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    expires_at: Optional[datetime.datetime] = None

    def is_expired(self) -> bool:
        """Check if the credential is expired.

        Returns:
            True if the credential is expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return self.expires_at < datetime.datetime.now()


@dataclass
class Identity:
    """An identity for authentication and authorization.

    An identity represents a user, service, or other entity that can be
    authenticated and authorized to access resources.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    credentials: List[Credential] = field(default_factory=list)
    permissions: Dict[str, PermissionLevel] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

    def has_permission(self, resource: str, level: PermissionLevel) -> bool:
        """Check if the identity has a permission.

        Args:
            resource: The resource to check permissions for
            level: The permission level to check

        Returns:
            True if the identity has the permission, False otherwise
        """
        # Check for exact resource match
        if resource in self.permissions:
            return self.permissions[resource].value >= level.value

        # Check for wildcard matches
        parts = resource.split(":")
        for i in range(len(parts)):
            wildcard = ":".join(parts[:i] + ["*"])
            if wildcard in self.permissions:
                return self.permissions[wildcard].value >= level.value

        return False


class AuthenticationError(Exception):
    """Error raised when authentication fails."""

    pass


class AuthorizationError(Exception):
    """Error raised when authorization fails."""

    pass


class Authenticator(ABC):
    """Base class for authenticators.

    Authenticators are responsible for authenticating credentials and
    returning the associated identity.
    """

    @abstractmethod
    def authenticate(self, credential: Credential) -> Optional[Identity]:
        """Authenticate a credential.

        Args:
            credential: The credential to authenticate

        Returns:
            The authenticated identity, or None if authentication fails

        Raises:
            AuthenticationError: If authentication fails with an error
        """
        pass


class Authorizer(ABC):
    """Base class for authorizers.

    Authorizers are responsible for checking if an identity is authorized
    to access a resource at a given permission level.
    """

    @abstractmethod
    def authorize(
        self, identity: Identity, resource: str, level: PermissionLevel
    ) -> bool:
        """Check if an identity is authorized to access a resource.

        Args:
            identity: The identity to check
            resource: The resource to check access for
            level: The permission level to check

        Returns:
            True if the identity is authorized, False otherwise

        Raises:
            AuthorizationError: If authorization fails with an error
        """
        pass


class CredentialStore(ABC):
    """Base class for credential stores."""

    @abstractmethod
    def add_credential(self, credential: Credential) -> None:
        """Add a credential to the store.

        Args:
            credential: The credential to add
        """
        pass

    @abstractmethod
    def get_credential(self, id: str) -> Optional[Credential]:
        """Get a credential by ID.

        Args:
            id: The ID of the credential to get

        Returns:
            The credential, or None if not found
        """
        pass

    @abstractmethod
    def get_credentials_by_key(self, key: str) -> List[Credential]:
        """Get credentials by key.

        Args:
            key: The key to search for

        Returns:
            A list of credentials with the given key
        """
        pass

    @abstractmethod
    def update_credential(self, credential: Credential) -> None:
        """Update a credential in the store.

        Args:
            credential: The credential to update
        """
        pass

    @abstractmethod
    def delete_credential(self, id: str) -> None:
        """Delete a credential from the store.

        Args:
            id: The ID of the credential to delete
        """
        pass


class IdentityStore(ABC):
    """Base class for identity stores."""

    @abstractmethod
    def add_identity(self, identity: Identity) -> None:
        """Add an identity to the store.

        Args:
            identity: The identity to add
        """
        pass

    @abstractmethod
    def get_identity(self, id: str) -> Optional[Identity]:
        """Get an identity by ID.

        Args:
            id: The ID of the identity to get

        Returns:
            The identity, or None if not found
        """
        pass

    @abstractmethod
    def get_identity_by_name(self, name: str) -> Optional[Identity]:
        """Get an identity by name.

        Args:
            name: The name of the identity to get

        Returns:
            The identity, or None if not found
        """
        pass

    @abstractmethod
    def update_identity(self, identity: Identity) -> None:
        """Update an identity in the store.

        Args:
            identity: The identity to update
        """
        pass

    @abstractmethod
    def delete_identity(self, id: str) -> None:
        """Delete an identity from the store.

        Args:
            id: The ID of the identity to delete
        """
        pass


class ApiKeyAuthenticator(Authenticator):
    """Authenticator for API keys.

    This authenticator authenticates API keys by looking them up in a
    credential store and finding the associated identity.
    """

    def __init__(
        self, credential_store: CredentialStore, identity_store: IdentityStore
    ):
        """Initialize the authenticator.

        Args:
            credential_store: The credential store to use
            identity_store: The identity store to use
        """
        self.credential_store = credential_store
        self.identity_store = identity_store

    def authenticate(self, credential: Credential) -> Optional[Identity]:
        """Authenticate an API key.

        Args:
            credential: The credential to authenticate

        Returns:
            The authenticated identity, or None if authentication fails

        Raises:
            AuthenticationError: If authentication fails with an error
        """
        if credential.auth_type != AuthType.API_KEY:
            raise AuthenticationError("Invalid authentication type")

        # Get credentials with the same key
        credentials = self.credential_store.get_credentials_by_key(credential.key)
        if not credentials:
            return None

        # Find a valid credential
        valid_credential = None
        for cred in credentials:
            if not cred.is_expired():
                valid_credential = cred
                break

        if valid_credential is None:
            return None

        # Find the identity with this credential
        for identity_id in [
            cred.metadata.get("identity_id")
            for cred in credentials
            if not cred.is_expired()
        ]:
            if identity_id:
                identity = self.identity_store.get_identity(identity_id)
                if identity:
                    return identity

        return None


class SimpleAuthorizer(Authorizer):
    """Simple authorizer that checks permissions directly on the identity.

    This authorizer checks if the identity has the required permission
    for the resource.
    """

    def authorize(
        self, identity: Identity, resource: str, level: PermissionLevel
    ) -> bool:
        """Check if an identity is authorized to access a resource.

        Args:
            identity: The identity to check
            resource: The resource to check access for
            level: The permission level to check

        Returns:
            True if the identity is authorized, False otherwise
        """
        return identity.has_permission(resource, level)


class MemoryCredentialStore(CredentialStore):
    """In-memory credential store.

    This credential store keeps credentials in memory.
    """

    def __init__(self):
        """Initialize the credential store."""
        self.credentials: Dict[str, Credential] = {}
        self.key_index: Dict[str, List[str]] = {}

    def add_credential(self, credential: Credential) -> None:
        """Add a credential to the store.

        Args:
            credential: The credential to add
        """
        self.credentials[credential.id] = credential
        if credential.key:
            if credential.key not in self.key_index:
                self.key_index[credential.key] = []
            self.key_index[credential.key].append(credential.id)

    def get_credential(self, id: str) -> Optional[Credential]:
        """Get a credential by ID.

        Args:
            id: The ID of the credential to get

        Returns:
            The credential, or None if not found
        """
        return self.credentials.get(id)

    def get_credentials_by_key(self, key: str) -> List[Credential]:
        """Get credentials by key.

        Args:
            key: The key to search for

        Returns:
            A list of credentials with the given key
        """
        credential_ids = self.key_index.get(key, [])
        return [self.credentials[id] for id in credential_ids if id in self.credentials]

    def update_credential(self, credential: Credential) -> None:
        """Update a credential in the store.

        Args:
            credential: The credential to update

        Raises:
            KeyError: If the credential is not in the store
        """
        if credential.id not in self.credentials:
            raise KeyError(f"Credential {credential.id} not found")

        # Remove from key index if key changed
        old_credential = self.credentials[credential.id]
        if old_credential.key != credential.key:
            if old_credential.key in self.key_index:
                self.key_index[old_credential.key] = [
                    id
                    for id in self.key_index[old_credential.key]
                    if id != credential.id
                ]
                if not self.key_index[old_credential.key]:
                    del self.key_index[old_credential.key]

            # Add to key index with new key
            if credential.key:
                if credential.key not in self.key_index:
                    self.key_index[credential.key] = []
                self.key_index[credential.key].append(credential.id)

        # Update credential
        self.credentials[credential.id] = credential

    def delete_credential(self, id: str) -> None:
        """Delete a credential from the store.

        Args:
            id: The ID of the credential to delete

        Raises:
            KeyError: If the credential is not in the store
        """
        if id not in self.credentials:
            raise KeyError(f"Credential {id} not found")

        # Remove from key index
        credential = self.credentials[id]
        if credential.key in self.key_index:
            self.key_index[credential.key] = [
                cred_id for cred_id in self.key_index[credential.key] if cred_id != id
            ]
            if not self.key_index[credential.key]:
                del self.key_index[credential.key]

        # Delete credential
        del self.credentials[id]


class MemoryIdentityStore(IdentityStore):
    """In-memory identity store.

    This identity store keeps identities in memory.
    """

    def __init__(self):
        """Initialize the identity store."""
        self.identities: Dict[str, Identity] = {}
        self.name_index: Dict[str, str] = {}

    def add_identity(self, identity: Identity) -> None:
        """Add an identity to the store.

        Args:
            identity: The identity to add
        """
        self.identities[identity.id] = identity
        if identity.name:
            self.name_index[identity.name] = identity.id

    def get_identity(self, id: str) -> Optional[Identity]:
        """Get an identity by ID.

        Args:
            id: The ID of the identity to get

        Returns:
            The identity, or None if not found
        """
        return self.identities.get(id)

    def get_identity_by_name(self, name: str) -> Optional[Identity]:
        """Get an identity by name.

        Args:
            name: The name of the identity to get

        Returns:
            The identity, or None if not found
        """
        identity_id = self.name_index.get(name)
        if identity_id:
            return self.identities.get(identity_id)
        return None

    def update_identity(self, identity: Identity) -> None:
        """Update an identity in the store.

        Args:
            identity: The identity to update

        Raises:
            KeyError: If the identity is not in the store
        """
        if identity.id not in self.identities:
            raise KeyError(f"Identity {identity.id} not found")

        # Remove from name index if name changed
        old_identity = self.identities[identity.id]
        if old_identity.name != identity.name:
            if old_identity.name in self.name_index:
                del self.name_index[old_identity.name]

            # Add to name index with new name
            if identity.name:
                self.name_index[identity.name] = identity.id

        # Update identity
        self.identities[identity.id] = identity

    def delete_identity(self, id: str) -> None:
        """Delete an identity from the store.

        Args:
            id: The ID of the identity to delete

        Raises:
            KeyError: If the identity is not in the store
        """
        if id not in self.identities:
            raise KeyError(f"Identity {id} not found")

        # Remove from name index
        identity = self.identities[id]
        if identity.name in self.name_index:
            del self.name_index[identity.name]

        # Delete identity
        del self.identities[id]


class SecurityManager:
    """Manager for security operations.

    The security manager provides a high-level interface for security operations,
    including authentication, authorization, and credential management.
    """

    def __init__(
        self,
        credential_store: CredentialStore,
        identity_store: IdentityStore,
        authenticator: Authenticator,
        authorizer: Authorizer,
    ):
        """Initialize the security manager.

        Args:
            credential_store: The credential store to use
            identity_store: The identity store to use
            authenticator: The authenticator to use
            authorizer: The authorizer to use
        """
        self.credential_store = credential_store
        self.identity_store = identity_store
        self.authenticator = authenticator
        self.authorizer = authorizer

    def authenticate(self, credential: Credential) -> Optional[Identity]:
        """Authenticate an identity using a credential.

        Args:
            credential: The credential to authenticate with

        Returns:
            The authenticated identity, or None if authentication fails

        Raises:
            AuthenticationError: If authentication fails with an error
        """
        return self.authenticator.authenticate(credential)

    def authorize(
        self, identity: Identity, resource: str, level: PermissionLevel
    ) -> bool:
        """Check if an identity is authorized to access a resource.

        Args:
            identity: The identity to check
            resource: The resource to check access for
            level: The permission level to check

        Returns:
            True if the identity is authorized, False otherwise

        Raises:
            AuthorizationError: If authorization fails with an error
        """
        return self.authorizer.authorize(identity, resource, level)

    def create_api_key(
        self, identity_id: str, expires_in: Optional[datetime.timedelta] = None
    ) -> Credential:
        """Create an API key for an identity.

        Args:
            identity_id: The ID of the identity to create the API key for
            expires_in: Optional expiration time for the API key

        Returns:
            The created API key credential

        Raises:
            KeyError: If the identity is not found
        """
        # Check if identity exists
        identity = self.identity_store.get_identity(identity_id)
        if not identity:
            raise KeyError(f"Identity {identity_id} not found")

        # Create API key
        key = secrets.token_urlsafe(32)
        expires_at = None
        if expires_in:
            expires_at = datetime.datetime.now() + expires_in

        # Create credential
        credential = Credential(
            auth_type=AuthType.API_KEY,
            key=key,
            expires_at=expires_at,
            metadata={"identity_id": identity_id},
        )

        # Add credential to store
        self.credential_store.add_credential(credential)

        # Add credential to identity
        identity.credentials.append(credential)
        self.identity_store.update_identity(identity)

        return credential

    def create_identity(
        self, name: str, permissions: Optional[Dict[str, PermissionLevel]] = None
    ) -> Identity:
        """Create a new identity.

        Args:
            name: The name of the identity
            permissions: Optional permissions for the identity

        Returns:
            The created identity
        """
        # Create identity
        identity = Identity(
            name=name,
            permissions=permissions or {},
        )

        # Add identity to store
        self.identity_store.add_identity(identity)

        return identity

    def revoke_credential(self, credential_id: str) -> None:
        """Revoke a credential.

        Args:
            credential_id: The ID of the credential to revoke

        Raises:
            KeyError: If the credential is not found
        """
        # Get credential
        credential = self.credential_store.get_credential(credential_id)
        if not credential:
            raise KeyError(f"Credential {credential_id} not found")

        # Revoke credential by setting expiration to now
        credential.expires_at = datetime.datetime.now()
        self.credential_store.update_credential(credential)

        # Update identity if needed
        identity_id = credential.metadata.get("identity_id")
        if identity_id:
            identity = self.identity_store.get_identity(identity_id)
            if identity:
                # Update credential in identity
                for i, cred in enumerate(identity.credentials):
                    if cred.id == credential_id:
                        identity.credentials[i] = credential
                        break
                self.identity_store.update_identity(identity)

    def update_permissions(
        self, identity_id: str, permissions: Dict[str, PermissionLevel]
    ) -> None:
        """Update permissions for an identity.

        Args:
            identity_id: The ID of the identity to update
            permissions: The new permissions for the identity

        Raises:
            KeyError: If the identity is not found
        """
        # Get identity
        identity = self.identity_store.get_identity(identity_id)
        if not identity:
            raise KeyError(f"Identity {identity_id} not found")

        # Update permissions
        identity.permissions = permissions
        self.identity_store.update_identity(identity)


def create_security_manager() -> SecurityManager:
    """Create a default security manager.

    This function creates a security manager with in-memory stores and
    default authenticator and authorizer.

    Returns:
        A security manager
    """
    credential_store = MemoryCredentialStore()
    identity_store = MemoryIdentityStore()
    authenticator = ApiKeyAuthenticator(credential_store, identity_store)
    authorizer = SimpleAuthorizer()

    return SecurityManager(
        credential_store=credential_store,
        identity_store=identity_store,
        authenticator=authenticator,
        authorizer=authorizer,
    )
