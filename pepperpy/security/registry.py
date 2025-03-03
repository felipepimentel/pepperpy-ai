"""Registry for security providers."""

from typing import Dict, List, Type

from pepperpy.security.base import SecurityManager

# Registry of security providers
_SECURITY_REGISTRY: Dict[str, Type[SecurityManager]] = {}


def register_security_provider(
    name: str, provider_class: Type[SecurityManager],
) -> None:
    """Register a security provider class.

    Args:
        name: Name of the security provider
        provider_class: Security provider class

    """
    _SECURITY_REGISTRY[name] = provider_class


def get_security_provider_class(name: str) -> Type[SecurityManager]:
    """Get a security provider class by name.

    Args:
        name: Name of the security provider

    Returns:
        Type[SecurityManager]: Security provider class

    Raises:
        ValueError: If security provider is not found

    """
    if name not in _SECURITY_REGISTRY:
        raise ValueError(f"Security provider '{name}' not found in registry")
    return _SECURITY_REGISTRY[name]


def list_security_providers() -> List[str]:
    """List all registered security providers.

    Returns:
        List[str]: List of security provider names

    """
    return list(_SECURITY_REGISTRY.keys())


def get_security_registry() -> Dict[str, Type[SecurityManager]]:
    """Get the security provider registry.

    Returns:
        Dict[str, Type[SecurityManager]]: Copy of the security provider registry

    """
    return _SECURITY_REGISTRY.copy()
