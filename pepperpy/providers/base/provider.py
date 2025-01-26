"""Base provider interface for Pepperpy."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class ProviderConfig:
    """Configuration for providers."""
    type: str
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseProvider(ABC):
    """Base class for all providers in the system."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the provider with configuration."""
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized 