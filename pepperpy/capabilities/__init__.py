"""Capabilities module for PepperPy.

This module provides various capabilities that can be used by agents and other components.
"""

from enum import Enum, auto

# Import internal implementations
from pepperpy.capabilities.base import BaseCapability, CapabilityConfig

# Re-export public interfaces
from pepperpy.capabilities.public import (
    TaskCapability,
    TaskRegistry,
    TaskScheduler,
)


class CapabilityType(Enum):
    """Types of capabilities supported by the system."""

    MEMORY = auto()
    STORAGE = auto()
    TASK = auto()
    STREAMING = auto()
    LOGGING = auto()
    METRICS = auto()
    TRACING = auto()
    SECURITY = auto()
    NETWORKING = auto()
    SCHEDULING = auto()


__all__ = [
    # Public interfaces
    "TaskCapability",
    "TaskRegistry",
    "TaskScheduler",
    # Implementation classes
    "BaseCapability",
    "CapabilityConfig",
    "CapabilityType",
]
