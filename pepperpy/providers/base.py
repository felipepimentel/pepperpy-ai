"""Base functionality for providers in PepperPy.

This module defines the base functionality for providers in the PepperPy framework.
Providers are responsible for integrating with external services and APIs.

This module re-exports the core BaseProvider and ProviderRegistry classes.
"""

from pepperpy.core.base_provider import (
    BaseProvider,
    ProviderRegistry,
    provider_registry,
)

# Re-export the core classes
__all__ = [
    "BaseProvider",
    "ProviderRegistry",
    "provider_registry",
]
