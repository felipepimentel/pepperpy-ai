"""Base classes and interfaces for PepperPy core components.

This module provides the foundational classes and interfaces that form the
core of the PepperPy framework. These components are used throughout the
framework to provide consistent behavior and interfaces.

It includes:
- Base component classes
- Common interfaces
- Core client functionality
"""

from abc import ABC, abstractmethod


class BaseComponent(ABC):
    """Base class for all components in the system."""

    def __init__(self, **kwargs):
        """Initialize the component with optional keyword arguments."""
        self.config = kwargs

    @abstractmethod
    def initialize(self):
        """Initialize the component. Must be implemented by subclasses."""
        pass


class BaseProvider(BaseComponent):
    """Base class for all providers in the system."""

    @abstractmethod
    def validate(self):
        """Validate the provider configuration. Must be implemented by subclasses."""
        pass


from .common import BaseComponent as LegacyBaseComponent
from .manager import BaseManager, ComponentState

__all__ = [
    "BaseComponent",
    "BaseProvider",
    "LegacyBaseComponent",
    "BaseManager",
    "ComponentState",
]
