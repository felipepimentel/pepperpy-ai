"""Integration plugins for PepperPy.

This module provides access to integration plugins for various external services.
"""

from plugins.integration.base import (
    IntegrationError,
    IntegrationProvider,
    create_integration_provider,
)

__all__ = [
    "IntegrationError",
    "IntegrationProvider",
    "create_integration_provider",
]
