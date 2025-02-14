"""Core capabilities management module.

This module provides a unified system for managing agent capabilities,
including error handling, type definitions, and common functionality.
"""

from .base import BaseCapability, Capability, CapabilityConfig
from .errors import (
    CapabilityCleanupError,
    CapabilityConfigError,
    CapabilityError,
    CapabilityInitError,
    CapabilityNotFoundError,
)
from .registry import CapabilityRegistry

# Create global registry instance
registry = CapabilityRegistry()

__all__ = [
    "BaseCapability",
    "Capability",
    "CapabilityConfig",
    "CapabilityRegistry",
    "registry",
    # Error types
    "CapabilityError",
    "CapabilityNotFoundError",
    "CapabilityConfigError",
    "CapabilityInitError",
    "CapabilityCleanupError",
]
