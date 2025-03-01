"""
Base provider module for {domain_name}.

This module defines the base interfaces and classes for {domain_name} providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.base import Component
from pepperpy.providers.agent.base import BaseProvider


class Base{domain_class}Provider(BaseProvider, ABC):
    """
    Base class for {domain_name} providers.
    
    This class defines the interface that all {domain_name} providers must implement.
    """
    
    provider_type = "{domain_name}"
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the provider with any necessary setup.
        
        This method is called when the provider is first created.
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate the provider configuration.
        
        Returns:
            bool: True if the configuration is valid, False otherwise.
        """
        pass
    
    # Add domain-specific abstract methods here
