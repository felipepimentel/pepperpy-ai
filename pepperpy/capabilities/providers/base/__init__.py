"""Base provider capabilities.

This module defines the base provider capabilities and interfaces.
"""

from pepperpy.capabilities.providers.base.base import ProviderCapability
from pepperpy.capabilities.providers.base.types import ProviderConfig

__all__ = [
    "ProviderCapability",
    "ProviderConfig",
]
