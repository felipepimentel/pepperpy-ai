"""Provider Registry implementation for Pepperpy."""
from typing import Type, Dict, Any, TypeVar, Generic

T = TypeVar('T')

class ProviderRegistry(Generic[T]):
    """A generic registry for managing providers."""
    
    _registry: Dict[str, Type[T]] = {}
    
    @classmethod
    def register(cls, name: str):
        """Register a provider class.
        
        Args:
            name: The name to register the provider under.
            
        Returns:
            A decorator that registers the provider class.
        """
        def decorator(provider_cls: Type[T]) -> Type[T]:
            cls._registry[name] = provider_cls
            return provider_cls
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Type[T]:
        """Get a registered provider class.
        
        Args:
            name: The name of the provider to get.
            
        Returns:
            The registered provider class.
            
        Raises:
            ValueError: If the provider is not registered.
        """
        if name not in cls._registry:
            raise ValueError(f"Provider '{name}' not registered.")
        return cls._registry[name]
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered providers.
        
        Returns:
            A list of registered provider names.
        """
        return list(cls._registry.keys()) 