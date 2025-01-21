"""Base interface for LLM providers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, TypeVar, ClassVar

T = TypeVar('T', bound='BaseLLMProvider')

class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    _registry: ClassVar[Dict[str, Type['BaseLLMProvider']]] = {}
    
    @classmethod
    def register(cls, name: str) -> Any:
        """Register a provider class.
        
        Args:
            name: Name to register the provider under.
            
        Returns:
            Decorator function.
        """
        def decorator(provider_cls: Type[T]) -> Type[T]:
            cls._registry[name] = provider_cls
            return provider_cls
        return decorator
    
    @classmethod
    def get_provider(cls, name: str) -> Type['BaseLLMProvider']:
        """Get a registered provider class.
        
        Args:
            name: Name of the provider.
            
        Returns:
            Provider class.
            
        Raises:
            ValueError: If provider is not registered.
        """
        if name not in cls._registry:
            raise ValueError(f"Provider '{name}' not registered")
        return cls._registry[name]
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM provider.
        
        Args:
            config: Configuration dictionary for the provider.
        """
        self.config = config
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider.
        
        Returns:
            True if initialization was successful.
            
        Raises:
            ValueError: If initialization fails.
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt.
        
        Args:
            prompt: The input prompt.
            **kwargs: Additional provider-specific arguments.
            
        Returns:
            The generated text.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs):
        """Stream text generation from a prompt.
        
        Args:
            prompt: The input prompt.
            **kwargs: Additional provider-specific arguments.
            
        Yields:
            Generated text chunks.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized") 