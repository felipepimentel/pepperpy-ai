"""Base adapter interface for provider integration."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

from .provider import BaseProvider, ProviderConfig

T = TypeVar('T', bound=BaseProvider)

class BaseAdapter(Generic[T], ABC):
    """Base adapter for provider integration."""
    
    def __init__(self, provider: T):
        """Initialize the adapter with a provider."""
        self.provider = provider
    
    @abstractmethod
    async def adapt(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt input data for provider processing."""
        pass
    
    @abstractmethod
    async def transform(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform provider output to standard format."""
        pass
    
    @property
    def config(self) -> ProviderConfig:
        """Get provider configuration."""
        return self.provider.config 