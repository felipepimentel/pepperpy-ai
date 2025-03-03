"""Factory for creating security components."""

from typing import Any, Dict, Optional

from pepperpy.security.base import SecurityManager
from pepperpy.security.registry import get_security_provider_class


class SecurityError(Exception):
    """Base exception for security-related errors."""



def create_security_provider(
    provider: str, config: Optional[Dict[str, Any]] = None, **kwargs,
) -> SecurityManager:
    """Create a security provider instance.

    Args:
        provider: Name of the security provider to create
        config: Optional configuration dictionary
        **kwargs: Additional provider-specific parameters

    Returns:
        SecurityManager: Security provider instance

    Raises:
        SecurityError: If provider creation fails

    """
    try:
        # Get provider class from registry
        provider_class = get_security_provider_class(provider)

        # Merge config and kwargs
        provider_config = {}
        if config:
            provider_config.update(config)
        provider_config.update(kwargs)

        # Create provider instance
        return provider_class(**provider_config)
    except Exception as e:
        raise SecurityError(
            f"Failed to create security provider '{provider}': {e}",
        ) from e
