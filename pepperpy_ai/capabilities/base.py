"""Base capability module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pepperpy_ai.providers.base import BaseProvider


@dataclass
class CapabilityConfig:
    """Base capability configuration.
    
    Attributes:
        name: Configuration name
        description: Configuration description
        metadata: Additional metadata
    """
    name: str
    description: str
    metadata: Optional[Dict[str, Any]] = None


class BaseCapability(ABC):
    """Base capability class."""
    
    def __init__(self, config: CapabilityConfig, provider: BaseProvider) -> None:
        """Initialize the capability.
        
        Args:
            config: The capability configuration
            provider: The AI provider to use
        """
        self.config = config
        self.provider = provider
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the capability."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass 