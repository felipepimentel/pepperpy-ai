"""Base embeddings provider implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, ClassVar

from ...interfaces import EmbeddingProvider

logger = logging.getLogger(__name__)

class BaseEmbeddingProvider(ABC, EmbeddingProvider):
    """Base class for embedding providers."""
    
    _registry: ClassVar[Dict[str, Type['BaseEmbeddingProvider']]] = {}
    
    @classmethod
    def register(cls, name: str) -> Any:
        """Register a provider class.
        
        Args:
            name: Name to register the provider under.
            
        Returns:
            Decorator function.
        """
        def decorator(provider_cls: Type['BaseEmbeddingProvider']) -> Type['BaseEmbeddingProvider']:
            cls._registry[name] = provider_cls
            return provider_cls
        return decorator
    
    @classmethod
    def get_provider(cls, name: str) -> Type['BaseEmbeddingProvider']:
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
    
    async def embed(self, text: str) -> Dict[str, Any]:
        """Generate embeddings for text.
        
        Args:
            text: Input text.
            
        Returns:
            Embedding vectors.
            
        Raises:
            ValueError: If the provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        return await self._embed_impl(text)
    
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Implementation-specific initialization."""
        raise NotImplementedError
    
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Implementation-specific cleanup."""
        raise NotImplementedError
    
    @abstractmethod
    async def _embed_impl(self, text: str) -> Dict[str, Any]:
        """Implementation-specific text embedding.
        
        Args:
            text: Input text.
            
        Returns:
            Embedding vectors.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text.
        
        Args:
            text: Single text or list of texts to embed.
            
        Returns:
            Single embedding vector or list of embedding vectors.
            
        Raises:
            ValueError: If the provider is not initialized.
        """
        pass
    
    @abstractmethod
    async def embed_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed.
            batch_size: Size of batches to process.
            show_progress: Whether to show progress bar.
            
        Returns:
            List of embedding vectors.
            
        Raises:
            ValueError: If the provider is not initialized.
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings.
        
        Returns:
            Dimension of the embedding vectors.
            
        Raises:
            ValueError: If the provider is not initialized.
        """
        if self.dimension is None:
            raise ValueError("Provider not initialized")
        return self.dimension
    
    @abstractmethod
    async def similarity(
        self, 
        text1: str, 
        text2: str,
        metric: str = "cosine"
    ) -> float:
        """Calculate similarity between two texts.
        
        Args:
            text1: First text.
            text2: Second text.
            metric: Similarity metric to use (cosine, dot, euclidean).
            
        Returns:
            Similarity score between 0 and 1.
            
        Raises:
            ValueError: If the provider is not initialized or metric is invalid.
        """
        pass 