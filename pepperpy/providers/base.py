"""Base provider implementation and registry.

This module provides a standardized base for all providers and a centralized
registry system for provider management.
"""

from abc import ABC
from typing import Dict, Type, TypeVar, Generic, Optional, Any, ClassVar
from ..interfaces import Provider

T = TypeVar('T', bound=Provider)

class ProviderRegistry(Generic[T]):
    """Generic provider registry."""
    
    _instances: Dict[str, Dict[str, Dict[str, T]]] = {}
    _registry: Dict[str, Dict[str, Type[T]]] = {}
    
    @classmethod
    def register(cls, provider_type: str, name: str):
        """Register a provider class.
        
        Args:
            provider_type: Type of provider (e.g. "llm", "vector_store")
            name: Name to register under
            
        Returns:
            Registration decorator
        """
        def decorator(provider_cls: Type[T]) -> Type[T]:
            if provider_type not in cls._registry:
                cls._registry[provider_type] = {}
            cls._registry[provider_type][name] = provider_cls
            return provider_cls
        return decorator
    
    @classmethod
    def get_provider(cls, provider_type: str, name: str) -> Type[T]:
        """Get a registered provider class.
        
        Args:
            provider_type: Type of provider
            name: Provider name
            
        Returns:
            Provider class
            
        Raises:
            ValueError: If provider not found
        """
        if provider_type not in cls._registry:
            raise ValueError(f"Unknown provider type: {provider_type}")
        if name not in cls._registry[provider_type]:
            raise ValueError(f"Provider '{name}' not registered for type {provider_type}")
        return cls._registry[provider_type][name]
    
    @classmethod
    def list_providers(cls, provider_type: str) -> list[str]:
        """List registered providers of a type.
        
        Args:
            provider_type: Type of provider
            
        Returns:
            List of provider names
        """
        if provider_type not in cls._registry:
            return []
        return list(cls._registry[provider_type].keys())
    
    @classmethod
    def get_instance(cls, provider_type: str, name: str, instance_id: str) -> Optional[T]:
        """Get a provider instance.
        
        Args:
            provider_type: Type of provider
            name: Provider name
            instance_id: Instance identifier
            
        Returns:
            Provider instance if found, None otherwise
        """
        try:
            return cls._instances[provider_type][name][instance_id]
        except KeyError:
            return None
    
    @classmethod
    def register_instance(cls, provider_type: str, name: str, instance_id: str, instance: T) -> None:
        """Register a provider instance.
        
        Args:
            provider_type: Type of provider
            name: Provider name
            instance_id: Instance identifier
            instance: Provider instance
        """
        if provider_type not in cls._instances:
            cls._instances[provider_type] = {}
        if name not in cls._instances[provider_type]:
            cls._instances[provider_type][name] = {}
        cls._instances[provider_type][name][instance_id] = instance

class BaseProvider(ABC, Provider):
    """Base class for all providers."""
    
    registry: ClassVar[ProviderRegistry] = ProviderRegistry()
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize provider.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self.is_initialized = False
        self._instance_id: Optional[str] = None
    
    @property
    def instance_id(self) -> Optional[str]:
        """Get instance ID."""
        return self._instance_id
    
    async def initialize(self) -> None:
        """Initialize the provider.
        
        This method should be called before using the provider.
        It will call the implementation-specific _initialize_impl() method.
        
        Raises:
            ValueError: If initialization fails
        """
        if self.is_initialized:
            return
            
        try:
            await self._initialize_impl()
            self.is_initialized = True
        except Exception as e:
            await self.cleanup()
            raise ValueError(f"Initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up provider resources.
        
        This method should be called when the provider is no longer needed.
        It will call the implementation-specific _cleanup_impl() method.
        """
        if not self.is_initialized:
            return
            
        try:
            await self._cleanup_impl()
        finally:
            self.is_initialized = False
    
    async def _initialize_impl(self) -> None:
        """Implementation-specific initialization.
        
        This method should be overridden by provider implementations.
        """
        raise NotImplementedError
    
    async def _cleanup_impl(self) -> None:
        """Implementation-specific cleanup.
        
        This method should be overridden by provider implementations.
        """
        raise NotImplementedError 