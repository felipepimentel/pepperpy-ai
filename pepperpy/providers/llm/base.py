"""Base LLM provider implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, ClassVar, AsyncGenerator, AsyncIterator

from ...interfaces import LLMProvider
from ..base import BaseProvider

logger = logging.getLogger(__name__)

class BaseLLMProvider(BaseProvider, LLMProvider):
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
        def decorator(provider_cls: Type['BaseLLMProvider']) -> Type['BaseLLMProvider']:
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
        """Initialize the provider.
        
        Args:
            config: Provider configuration.
        """
        self.config = config
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the provider.
        
        Raises:
            ValueError: If initialization fails.
        """
        if self.is_initialized:
            return
            
        try:
            await self._initialize_impl()
            self.is_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize provider: {str(e)}")
            await self.cleanup()
            raise ValueError(f"Provider initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        try:
            await self._cleanup_impl()
        finally:
            self.is_initialized = False
    
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from a prompt.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional generation parameters.
            
        Returns:
            Generated text.
            
        Raises:
            ValueError: If the provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        return await self._generate_impl(prompt, **kwargs)
    
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Implementation-specific initialization."""
        raise NotImplementedError
    
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Implementation-specific cleanup."""
        raise NotImplementedError
    
    @abstractmethod
    async def _generate_impl(self, prompt: str, **kwargs: Any) -> str:
        """Implementation-specific text generation.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional generation parameters.
            
        Returns:
            Generated text.
        """
        raise NotImplementedError
    
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """Stream text generation from a prompt.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional generation parameters.
            
        Yields:
            Generated text chunks.
            
        Raises:
            ValueError: If provider not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        generator = self._stream_impl(prompt, **kwargs)
        async for chunk in generator:
            yield chunk
    
    @abstractmethod
    async def _stream_impl(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """Implementation-specific streaming text generation.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional generation parameters.
            
        Yields:
            Generated text chunks.
        """
        raise NotImplementedError 