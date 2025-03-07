"""Provider capabilities for the Pepperpy framework.

This module provides provider capabilities that can be used by various components.
"""

from pepperpy.capabilities.providers.base.base import ProviderCapability
from pepperpy.capabilities.providers.base.types import ProviderConfig

__all__ = [
    "ProviderCapability",
    "ProviderConfig",
]
