"""LLM provider manager."""
from typing import AsyncIterator, Dict, List, Optional, Type, cast, Any

from pepperpy.llms.base_llm import BaseLLM
from pepperpy.llms.openrouter import OpenRouterProvider
from pepperpy.llms.types import LLMResponse, ProviderConfig, ProviderStats

PROVIDER_TYPES: Dict[str, Type[BaseLLM]] = {
    "openrouter": OpenRouterProvider
}

class LLMManager:
    """Manages LLM providers with fallback support."""
    
    def __init__(self) -> None:
        """Initialize LLM manager."""
        self.providers: Dict[str, BaseLLM] = {}
        self.configs: Dict[str, ProviderConfig] = {}
        self.is_initialized = False
    
    def register_provider(self, provider_type: str, provider_class: Type[BaseLLM]) -> None:
        """Register a provider type.
        
        Args:
            provider_type: Provider type identifier.
            provider_class: Provider class.
        """
        PROVIDER_TYPES[provider_type] = provider_class
    
    async def initialize(self, configs: Dict[str, Dict[str, Any]]) -> None:
        """Initialize providers.
        
        Args:
            configs: Provider configurations.
            
        Raises:
            ValueError: If provider initialization fails.
        """
        if self.is_initialized:
            return
        
        # Create provider configs
        for provider_name, config_dict in configs.items():
            config = ProviderConfig(**config_dict)
            self.configs[provider_name] = config
            
            # Create provider instance
            provider_class = PROVIDER_TYPES.get(config.type)
            if not provider_class:
                raise ValueError(f"Unknown provider type: {config.type}")
            
            provider = provider_class(config)
            await provider.initialize()
            self.providers[provider_name] = provider
        
        self.is_initialized = True
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        for provider in self.providers.values():
            await provider.cleanup()
        self.providers.clear()
        self.configs.clear()
        self.is_initialized = False
    
    def get_primary_provider(self) -> BaseLLM:
        """Get primary (non-fallback) provider.
        
        Returns:
            Primary provider.
            
        Raises:
            ValueError: If no primary provider is configured.
        """
        for provider_name, config in self.configs.items():
            if not config.is_fallback:
                return self.providers[provider_name]
        raise ValueError("No primary provider configured")
    
    def get_fallback_providers(self) -> List[BaseLLM]:
        """Get fallback providers in priority order.
        
        Returns:
            List of fallback providers.
        """
        fallbacks = [
            (name, config)
            for name, config in self.configs.items()
            if config.is_fallback
        ]
        fallbacks.sort(key=lambda x: x[1].priority)
        return [self.providers[name] for name, _ in fallbacks]
    
    async def generate(self, prompt: str) -> LLMResponse:
        """Generate text from prompt.
        
        Args:
            prompt: Input prompt.
            
        Returns:
            Generated text response.
            
        Raises:
            Exception: If generation fails for all providers.
        """
        if not self.is_initialized:
            raise Exception("LLM manager not initialized")
        
        # Try primary provider first
        try:
            primary = self.get_primary_provider()
            return await primary.generate(prompt)
        except Exception as e:
            # Try fallback providers in order
            last_error = e
            for provider in self.get_fallback_providers():
                try:
                    return await provider.generate(prompt)
                except Exception as e:
                    last_error = e
            
            raise last_error
    
    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """Generate text from prompt in streaming mode.
        
        Args:
            prompt: Input prompt.
            
        Returns:
            Iterator of generated text chunks.
            
        Raises:
            Exception: If generation fails for all providers.
        """
        if not self.is_initialized:
            raise Exception("LLM manager not initialized")
        
        # Try primary provider first
        try:
            primary = self.get_primary_provider()
            stream = await primary.generate_stream(prompt)
            async for chunk in stream:
                yield chunk
            return
        except Exception as e:
            # Try fallback providers in order
            last_error = e
            for provider in self.get_fallback_providers():
                try:
                    stream = await provider.generate_stream(prompt)
                    async for chunk in stream:
                        yield chunk
                    return
                except Exception as e:
                    last_error = e
            
            raise last_error
