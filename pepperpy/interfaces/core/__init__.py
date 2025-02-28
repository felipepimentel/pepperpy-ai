"""
Public Interface for core

This module provides a stable public interface for the core functionality.
It exposes the fundamental components and abstractions that form the
foundation of the PepperPy framework.

Classes:
    BaseComponent: Base class for all framework components
    ComponentState: Enumeration of component states
    Lifecycle: Protocol for lifecycle management
    Registry: Component registry system
    EventBus: Event system for component communication
"""

# Import public classes and functions from the implementation
from pepperpy.core.base import BaseComponent
from pepperpy.core.common.types.enums import ComponentState
from pepperpy.core.events import EventBus
from pepperpy.core.protocols import Lifecycle
from pepperpy.core.registry import Registry

__all__ = [
    "BaseComponent",
    "ComponentState",
    "Lifecycle",
    "Registry",
    "EventBus",
]
