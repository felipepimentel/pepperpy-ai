"""
Public Interface for capabilities

This module provides a stable public interface for the capabilities functionality.
It exposes the core capability abstractions and implementations that are
considered part of the public API.

Classes:
    BaseCapability: Base class for all capabilities
    CapabilityConfig: Configuration for capabilities
    CapabilityType: Enumeration of capability types
    ProviderCapability: Base class for provider capabilities
    ProviderConfig: Configuration for provider capabilities
"""

# Import public classes and functions from the implementation
from pepperpy.capabilities import CapabilityType
from pepperpy.capabilities.base import BaseCapability, CapabilityConfig
from pepperpy.capabilities.providers import ProviderCapability, ProviderConfig

__all__ = [
    "BaseCapability",
    "CapabilityConfig",
    "CapabilityType",
    "ProviderCapability",
    "ProviderConfig",
]
