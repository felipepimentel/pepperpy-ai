"""Public interfaces for PepperPy Capabilities module.

This module provides a stable public interface for the capabilities functionality.
It exposes the core capability abstractions and implementations that are
considered part of the public API.
"""

from pepperpy.capabilities.registry import (
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
