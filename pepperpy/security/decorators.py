"""Security decorators.

This module provides decorators for security-related functionality.
"""

from functools import wraps
from typing import Any, Callable, Optional, Set, TypeVar, cast

from pepperpy.security.errors import AuthenticationError, AuthorizationError
from pepperpy.security.provider import SecurityProvider
from pepperpy.security.types import Permission, SecurityContext, SecurityScope, Token

F = TypeVar("F", bound=Callable[..., Any])


def get_security_provider() -> SecurityProvider:
    """Get security provider instance.

    Returns:
        Security provider instance

    Raises:
        RuntimeError: If security provider is not initialized
    """
    from pepperpy.core.registry import get_provider

    provider = get_provider("security")
    if not provider or not isinstance(provider, SecurityProvider):
        raise RuntimeError("Security provider not initialized")
    return cast(SecurityProvider, provider)


def get_current_token() -> Token:
    """Get current token.

    Returns:
        Current token

    Raises:
        AuthenticationError: If no token is available
    """
    from pepperpy.core.context import get_context

    context = get_context()
    token = context.get("token")
    if not token or not isinstance(token, Token):
        raise AuthenticationError("No token available")
    return token


def get_security_context() -> SecurityContext:
    """Get current security context.

    Returns:
        Current security context

    Raises:
        AuthenticationError: If no security context is available
    """
    token = get_current_token()
    provider = get_security_provider()
    return provider.get_security_context(token)


def requires_authentication(f: F) -> F:
    """Require authentication.

    Args:
        f: Function to decorate

    Returns:
        Decorated function

    Raises:
        AuthenticationError: If authentication fails
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper function."""
        try:
            token = get_current_token()
            provider = get_security_provider()
            if not provider.validate_token(token):
                raise AuthenticationError("Invalid token")
            return f(*args, **kwargs)
        except Exception as e:
            raise AuthenticationError(str(e))

    return cast(F, wrapper)


def requires_scope(scope: SecurityScope) -> Callable[[F], F]:
    """Require security scope.

    Args:
        scope: Required scope

    Returns:
        Decorator function

    Raises:
        AuthorizationError: If scope check fails
    """

    def decorator(f: F) -> F:
        """Decorator function.

        Args:
            f: Function to decorate

        Returns:
            Decorated function
        """

        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function."""
            try:
                context = get_security_context()
                provider = get_security_provider()
                if not provider.has_scope(context, scope):
                    raise AuthorizationError(f"Missing required scope: {scope}")
                return f(*args, **kwargs)
            except Exception as e:
                raise AuthorizationError(str(e))

        return cast(F, wrapper)

    return decorator


def requires_scopes(scopes: Set[SecurityScope]) -> Callable[[F], F]:
    """Require multiple security scopes.

    Args:
        scopes: Required scopes

    Returns:
        Decorator function

    Raises:
        AuthorizationError: If scope check fails
    """

    def decorator(f: F) -> F:
        """Decorator function.

        Args:
            f: Function to decorate

        Returns:
            Decorated function
        """

        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function."""
            try:
                context = get_security_context()
                provider = get_security_provider()
                missing_scopes = {
                    scope for scope in scopes if not provider.has_scope(context, scope)
                }
                if missing_scopes:
                    raise AuthorizationError(
                        f"Missing required scopes: {', '.join(str(s) for s in missing_scopes)}"
                    )
                return f(*args, **kwargs)
            except Exception as e:
                raise AuthorizationError(str(e))

        return cast(F, wrapper)

    return decorator


def requires_permission(
    permission: Permission, resource: Optional[str] = None
) -> Callable[[F], F]:
    """Require permission.

    Args:
        permission: Required permission
        resource: Optional resource identifier

    Returns:
        Decorator function

    Raises:
        AuthorizationError: If permission check fails
    """

    def decorator(f: F) -> F:
        """Decorator function.

        Args:
            f: Function to decorate

        Returns:
            Decorated function
        """

        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function."""
            try:
                context = get_security_context()
                provider = get_security_provider()
                if not provider.has_permission(context, permission, resource):
                    raise AuthorizationError(
                        f"Missing required permission: {permission}"
                        + (f" on resource: {resource}" if resource else "")
                    )
                return f(*args, **kwargs)
            except Exception as e:
                raise AuthorizationError(str(e))

        return cast(F, wrapper)

    return decorator


def requires_role(role: str) -> Callable[[F], F]:
    """Require role.

    Args:
        role: Required role

    Returns:
        Decorator function

    Raises:
        AuthorizationError: If role check fails
    """

    def decorator(f: F) -> F:
        """Decorator function.

        Args:
            f: Function to decorate

        Returns:
            Decorated function
        """

        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function."""
            try:
                context = get_security_context()
                provider = get_security_provider()
                if not provider.has_role(context, role):
                    raise AuthorizationError(f"Missing required role: {role}")
                return f(*args, **kwargs)
            except Exception as e:
                raise AuthorizationError(str(e))

        return cast(F, wrapper)

    return decorator
