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
    MetricsManager: System for collecting and reporting metrics
    ConfigManager: Configuration management system
    ResourceManager: Resource allocation and management
"""

# Import public classes and functions from the implementation
from pepperpy.core.base import BaseComponent
from pepperpy.core.events import EventBus
from pepperpy.core.protocols.base import Lifecycle
from pepperpy.core.registry import Registry
from pepperpy.core.types.enums import ComponentState

# Import from submodules
from pepperpy.interfaces.core.config import ConfigManager
from pepperpy.interfaces.core.metrics import MetricsManager
from pepperpy.interfaces.core.resources import ResourceManager

__all__ = [
    # Base core classes
    "BaseComponent",
    "ComponentState",
    "Lifecycle",
    "Registry",
    "EventBus",
    # Management systems
    "ConfigManager",
    "MetricsManager",
    "ResourceManager",
]
