#!/usr/bin/env python3
"""
Example demonstrating the PepperPy Security module.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Set


class AuthenticationMethod(str, Enum):
    """Authentication methods supported by the security module."""

    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH = "oauth"
    BASIC = "basic"
    NONE = "none"


class Permission(str, Enum):
    """Permissions that can be granted to users."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass
class User:
    """Represents a user in the system."""

    id: str
    username: str
    email: str
    hashed_password: Optional[str] = None
    api_key: Optional[str] = None
    permissions: Set[Permission] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.permissions is None:
            self.permissions = {Permission.READ}
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def create(
        cls,
        username: str,
        email: str,
        password: Optional[str] = None,
        permissions: Optional[Set[Permission]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "User":
        """Create a new user with a unique ID."""
        user_id = str(uuid.uuid4())
        hashed_password = None

        if password:
            # In a real implementation, use a proper password hashing library
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Generate API key
        api_key = base64.b64encode(os.urandom(32)).decode()

        return cls(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            api_key=api_key,
            permissions=permissions,
            metadata=metadata,
        )


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class AuthorizationError(Exception):
    """Raised when a user doesn't have the required permissions."""

    pass


class SecurityManager:
    """Manages authentication and authorization."""

    def __init__(self) -> None:
        """Initialize the security manager."""
        self.users: Dict[str, User] = {}  # User ID -> User
        self.api_keys: Dict[str, str] = {}  # API Key -> User ID
        self.jwt_secret = base64.b64encode(os.urandom(32)).decode()

    def register_user(self, user: User) -> None:
        """Register a user with the security manager."""
        self.users[user.id] = user
        if user.api_key:
            self.api_keys[user.api_key] = user.id

    def authenticate_api_key(self, api_key: str) -> User:
        """Authenticate a user using an API key."""
        user_id = self.api_keys.get(api_key)
        if not user_id:
            raise AuthenticationError("Invalid API key")

        return self.users[user_id]

    def authenticate_password(self, username: str, password: str) -> User:
        """Authenticate a user using a username and password."""
        # In a real implementation, use a proper password hashing library
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        for user in self.users.values():
            if user.username == username and user.hashed_password == hashed_password:
                return user

        raise AuthenticationError("Invalid username or password")

    def create_jwt(self, user: User, expiry_seconds: int = 3600) -> str:
        """Create a JWT token for a user."""
        # In a real implementation, use a proper JWT library
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "permissions": [p.value for p in user.permissions],
            "exp": int(time.time()) + expiry_seconds,
            "iat": int(time.time()),
        }

        header_json = json.dumps(header).encode()
        payload_json = json.dumps(payload).encode()

        header_b64 = base64.b64encode(header_json).decode().rstrip("=")
        payload_b64 = base64.b64encode(payload_json).decode().rstrip("=")

        to_sign = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.jwt_secret.encode(),
            to_sign.encode(),
            hashlib.sha256,
        ).digest()
        signature_b64 = base64.b64encode(signature).decode().rstrip("=")

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def verify_jwt(self, token: str) -> User:
        """Verify a JWT token and return the associated user."""
        # In a real implementation, use a proper JWT library
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
            to_verify = f"{header_b64}.{payload_b64}"

            # Add padding if needed
            signature = base64.b64decode(
                signature_b64 + "=" * ((4 - len(signature_b64) % 4) % 4)
            )
            expected_signature = hmac.new(
                self.jwt_secret.encode(),
                to_verify.encode(),
                hashlib.sha256,
            ).digest()

            if not hmac.compare_digest(signature, expected_signature):
                raise AuthenticationError("Invalid JWT signature")

            # Add padding if needed
            payload_json = base64.b64decode(
                payload_b64 + "=" * ((4 - len(payload_b64) % 4) % 4)
            )
            payload = json.loads(payload_json)

            # Check expiry
            if payload.get("exp", 0) < time.time():
                raise AuthenticationError("JWT token has expired")

            user_id = payload.get("sub")
            if not user_id or user_id not in self.users:
                raise AuthenticationError("User not found")

            return self.users[user_id]

        except (ValueError, json.JSONDecodeError):
            raise AuthenticationError("Invalid JWT format")

    def authorize(self, user: User, required_permissions: Set[Permission]) -> bool:
        """Check if a user has the required permissions."""
        if Permission.ADMIN in user.permissions:
            return True

        if required_permissions.issubset(user.permissions):
            return True

        raise AuthorizationError(
            f"User {user.username} does not have the required permissions: "
            f"{', '.join(p.value for p in required_permissions - user.permissions)}"
        )


class SecureResource:
    """A resource that requires authentication and authorization to access."""

    def __init__(
        self,
        name: str,
        security_manager: SecurityManager,
        required_permissions: Set[Permission],
    ) -> None:
        """Initialize a secure resource."""
        self.name = name
        self.security_manager = security_manager
        self.required_permissions = required_permissions
        self.data: Dict[str, Any] = {}

    async def access(
        self,
        auth_method: AuthenticationMethod,
        credentials: Dict[str, str],
    ) -> Dict[str, Any]:
        """Access the resource using the provided authentication method and credentials."""
        user = None

        # Authenticate
        if auth_method == AuthenticationMethod.API_KEY:
            api_key = credentials.get("api_key")
            if not api_key:
                raise AuthenticationError("API key is required")
            user = self.security_manager.authenticate_api_key(api_key)

        elif auth_method == AuthenticationMethod.BASIC:
            username = credentials.get("username")
            password = credentials.get("password")
            if not username or not password:
                raise AuthenticationError("Username and password are required")
            user = self.security_manager.authenticate_password(username, password)

        elif auth_method == AuthenticationMethod.JWT:
            token = credentials.get("token")
            if not token:
                raise AuthenticationError("JWT token is required")
            user = self.security_manager.verify_jwt(token)

        else:
            raise AuthenticationError(
                f"Unsupported authentication method: {auth_method}"
            )

        # Authorize
        self.security_manager.authorize(user, self.required_permissions)

        # Access the resource
        return {
            "resource": self.name,
            "user": user.username,
            "data": self.data,
            "message": f"Successfully accessed {self.name} with {auth_method.value} authentication",
        }

    async def update(
        self,
        auth_method: AuthenticationMethod,
        credentials: Dict[str, str],
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update the resource using the provided authentication method and credentials."""
        # Ensure the user has WRITE permission
        required_permissions = self.required_permissions.union({Permission.WRITE})

        user = None

        # Authenticate
        if auth_method == AuthenticationMethod.API_KEY:
            api_key = credentials.get("api_key")
            if not api_key:
                raise AuthenticationError("API key is required")
            user = self.security_manager.authenticate_api_key(api_key)

        elif auth_method == AuthenticationMethod.BASIC:
            username = credentials.get("username")
            password = credentials.get("password")
            if not username or not password:
                raise AuthenticationError("Username and password are required")
            user = self.security_manager.authenticate_password(username, password)

        elif auth_method == AuthenticationMethod.JWT:
            token = credentials.get("token")
            if not token:
                raise AuthenticationError("JWT token is required")
            user = self.security_manager.verify_jwt(token)

        else:
            raise AuthenticationError(
                f"Unsupported authentication method: {auth_method}"
            )

        # Authorize
        self.security_manager.authorize(user, required_permissions)

        # Update the resource
        self.data.update(data)

        return {
            "resource": self.name,
            "user": user.username,
            "data": self.data,
            "message": f"Successfully updated {self.name} with {auth_method.value} authentication",
        }


async def main() -> None:
    """Run the security example."""
    print("PepperPy Security Example")
    print("========================")

    # Create a security manager
    security_manager = SecurityManager()

    # Create users with different permissions
    admin_user = User.create(
        username="admin",
        email="admin@example.com",
        password="admin123",
        permissions={Permission.ADMIN},
    )

    regular_user = User.create(
        username="user",
        email="user@example.com",
        password="user123",
        permissions={Permission.READ, Permission.WRITE},
    )

    readonly_user = User.create(
        username="readonly",
        email="readonly@example.com",
        password="readonly123",
        permissions={Permission.READ},
    )

    # Register users with the security manager
    security_manager.register_user(admin_user)
    security_manager.register_user(regular_user)
    security_manager.register_user(readonly_user)

    # Create a secure resource
    resource = SecureResource(
        name="sensitive-data",
        security_manager=security_manager,
        required_permissions={Permission.READ},
    )

    # Initialize resource data
    await resource.update(
        auth_method=AuthenticationMethod.API_KEY,
        credentials={"api_key": admin_user.api_key},
        data={"secret": "This is sensitive information"},
    )

    print("\nAccessing resource with different authentication methods:")

    # Access with API key
    try:
        result = await resource.access(
            auth_method=AuthenticationMethod.API_KEY,
            credentials={"api_key": regular_user.api_key},
        )
        print("\n1. API Key Authentication (Regular User):")
        print(f"   Message: {result['message']}")
        print(f"   Data: {result['data']}")
    except (AuthenticationError, AuthorizationError) as e:
        print("\n1. API Key Authentication (Regular User):")
        print(f"   Error: {str(e)}")

    # Access with basic authentication
    try:
        result = await resource.access(
            auth_method=AuthenticationMethod.BASIC,
            credentials={"username": "readonly", "password": "readonly123"},
        )
        print("\n2. Basic Authentication (Read-only User):")
        print(f"   Message: {result['message']}")
        print(f"   Data: {result['data']}")
    except (AuthenticationError, AuthorizationError) as e:
        print("\n2. Basic Authentication (Read-only User):")
        print(f"   Error: {str(e)}")

    # Access with JWT
    try:
        # Create JWT token for admin user
        jwt_token = security_manager.create_jwt(admin_user)

        result = await resource.access(
            auth_method=AuthenticationMethod.JWT,
            credentials={"token": jwt_token},
        )
        print("\n3. JWT Authentication (Admin User):")
        print(f"   Message: {result['message']}")
        print(f"   Data: {result['data']}")
    except (AuthenticationError, AuthorizationError) as e:
        print("\n3. JWT Authentication (Admin User):")
        print(f"   Error: {str(e)}")

    print("\nUpdating resource with different users:")

    # Update with read-only user (should fail)
    try:
        result = await resource.update(
            auth_method=AuthenticationMethod.BASIC,
            credentials={"username": "readonly", "password": "readonly123"},
            data={"new_secret": "This should not be added"},
        )
        print("\n1. Update with Read-only User:")
        print(f"   Message: {result['message']}")
        print(f"   Data: {result['data']}")
    except (AuthenticationError, AuthorizationError) as e:
        print("\n1. Update with Read-only User:")
        print(f"   Error: {str(e)}")

    # Update with regular user (should succeed)
    try:
        result = await resource.update(
            auth_method=AuthenticationMethod.API_KEY,
            credentials={"api_key": regular_user.api_key},
            data={"additional_info": "This should be added"},
        )
        print("\n2. Update with Regular User:")
        print(f"   Message: {result['message']}")
        print(f"   Data: {result['data']}")
    except (AuthenticationError, AuthorizationError) as e:
        print("\n2. Update with Regular User:")
        print(f"   Error: {str(e)}")

    # Invalid authentication
    try:
        result = await resource.access(
            auth_method=AuthenticationMethod.API_KEY,
            credentials={"api_key": "invalid-key"},
        )
        print("\n3. Invalid API Key:")
        print(f"   Message: {result['message']}")
    except (AuthenticationError, AuthorizationError) as e:
        print("\n3. Invalid API Key:")
        print(f"   Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
