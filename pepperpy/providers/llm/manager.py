"""LLM provider manager."""

import logging
from typing import AsyncIterator, Dict, List, Optional, Type, Any

from .base import BaseLLMProvider
from .huggingface import HuggingFaceProvider
from .types import LLMConfig

logger = logging.getLogger(__name__)

PROVIDER_TYPES: Dict[str, Type[BaseLLMProvider]] = {
    "huggingface": HuggingFaceProvider
}

class LLMManager:
    """LLM manager that manages LLM providers with fallback support."""
    
    def __init__(self) -> None:
        """Initialize LLM manager."""
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._configs: Dict[str, LLMConfig] = {}
        self._is_initialized = False
    
    @property
    def providers(self) -> Dict[str, BaseLLMProvider]:
        """Get registered providers."""
        return self._providers
    
    @property
    def configs(self) -> Dict[str, LLMConfig]:
        """Get provider configurations."""
        return self._configs
    
    def register_provider(self, provider_type: str, provider_class: Type[BaseLLMProvider]) -> None:
        """Register a provider type.
        
        Args:
            provider_type: Provider type identifier.
            provider_class: Provider class.
        """
        PROVIDER_TYPES[provider_type] = provider_class
    
    async def initialize(self, config: Dict[str, Dict[str, Any]]) -> None:
        """Initialize LLM providers.
        
        Args:
            config: Provider configurations.
            
        Raises:
            ValueError: If unknown provider type is encountered.
        """
        for name, provider_config in config.items():
            llm_config = LLMConfig(**provider_config)
            provider = HuggingFaceProvider(llm_config)
            await provider.initialize()
            self._providers[name] = provider
            self._configs[name] = llm_config
        
        self._is_initialized = True
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        for provider in self._providers.values():
            await provider.cleanup()
        self._providers.clear()
        self._configs.clear()
        self._is_initialized = False
    
    def get_primary_provider(self) -> BaseLLMProvider:
        """Get primary (non-fallback) provider.
        
        Returns:
            Primary provider.
            
        Raises:
            ValueError: If no primary provider is configured.
        """
        for name, config in self._configs.items():
            if not config.is_fallback:
                return self._providers[name]
        raise ValueError("No primary provider configured")
    
    def get_fallback_providers(self) -> List[BaseLLMProvider]:
        """Get fallback providers.
        
        Returns:
            List of fallback providers.
        """
        return [
            provider for name, provider in self._providers.items()
            if self._configs[name].is_fallback
        ]
    
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional generation parameters.
            
        Returns:
            Generated text.
            
        Raises:
            Exception: If generation fails for all providers.
        """
        if not self._is_initialized:
            raise Exception("LLM manager not initialized")
        
        # Try primary provider first
        try:
            primary = self.get_primary_provider()
            return await primary.generate(prompt, **kwargs)
        except Exception as e:
            last_error = e
        
        # Try fallback providers
        for provider in self.get_fallback_providers():
            try:
                return await provider.generate(prompt, **kwargs)
            except Exception as e:
                last_error = e
        
        raise last_error
    
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """Generate text from prompt in streaming mode.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional generation parameters.
            
        Returns:
            Iterator of generated text chunks.
            
        Raises:
            Exception: If generation fails for all providers.
        """
        if not self._is_initialized:
            raise Exception("LLM manager not initialized")
        
        # Try primary provider first
        try:
            primary = self.get_primary_provider()
            async for chunk in primary.stream(prompt, **kwargs):
                yield chunk
            return
        except Exception as e:
            last_error = e
        
        # Try fallback providers
        for provider in self.get_fallback_providers():
            try:
                async for chunk in provider.stream(prompt, **kwargs):
                    yield chunk
                return
            except Exception as e:
                last_error = e
        
        raise last_error 