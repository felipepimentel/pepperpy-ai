"""Base classes and interfaces for core functionality."""

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


__all__ = ["BaseComponent", "BaseProvider"]
