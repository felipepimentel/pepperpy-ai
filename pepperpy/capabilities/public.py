"""Public API for the PepperPy capabilities module.

This module exports the public API for the PepperPy capabilities module.
It includes capability registry, functions for managing capabilities, and capability types.
"""

from pepperpy.capabilities.core import (
    CapabilityRegistry,
    get_capability,
    has_capability,
    list_capabilities,
    list_capability_names,
    register_capability,
)
from pepperpy.core.interfaces import ProviderCapability

# Re-export everything
__all__ = [
    # Classes
    "CapabilityRegistry",
    "ProviderCapability",
    # Functions
    "get_capability",
    "has_capability",
    "list_capabilities",
    "list_capability_names",
    "register_capability",
]
