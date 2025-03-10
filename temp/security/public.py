"""Public interfaces for PepperPy Security module.

This module provides a stable public interface for the security functionality.
It exposes the core security abstractions and implementations that are
considered part of the public API.
"""

from pepperpy.security.core import (
    ApiKeyAuthenticator,
    AuthType,
    AuthenticationError,
    AuthorizationError,
    Authenticator,
    Authorizer,
    Credential,
    CredentialStore,
    Identity,
    IdentityStore,
    MemoryCredentialStore,
    MemoryIdentityStore,
    PermissionLevel,
    SecurityManager,
    SimpleAuthorizer,
    create_security_manager,
)

# Re-export everything from core
__all__ = [
    # Data classes
    "Credential",
    "Identity",
    
    # Enums
    "AuthType",
    "PermissionLevel",
    
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
    
    # Base classes
    "Authenticator",
    "Authorizer",
    "CredentialStore",
    "IdentityStore",
    
    # Implementations
    "ApiKeyAuthenticator",
    "MemoryCredentialStore",
    "MemoryIdentityStore",
    "SecurityManager",
    "SimpleAuthorizer",
    
    # Factory functions
    "create_security_manager",
] 