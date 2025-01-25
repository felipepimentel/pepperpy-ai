"""Base embedding provider implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from ...interfaces import EmbeddingProvider


class BaseEmbeddingProvider(ABC, EmbeddingProvider):
    """Base embedding provider implementation."""
    
    def __init__(
        self,
        name: str,
        dimension: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider.
        
        Args:
            name: Provider name
            dimension: Embedding dimension
            config: Optional configuration
        """
        if not name:
            raise ValueError("Provider name cannot be empty")
        if dimension <= 0:
            raise ValueError("Embedding dimension must be positive")
            
        self._name = name
        self._dimension = dimension
        self._config = config or {}
        self._initialized = False
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return self._name
        
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get provider configuration."""
        return self._config.copy()
        
    @property
    def is_initialized(self) -> bool:
        """Get initialization status."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize provider."""
        if self.is_initialized:
            return
            
        await self._initialize_impl()
        self._initialized = True
        
    async def cleanup(self) -> None:
        """Clean up provider."""
        if not self.is_initialized:
            return
            
        await self._cleanup_impl()
        self._initialized = False
        
    def validate(self) -> None:
        """Validate provider state."""
        if not self.name:
            raise ValueError("Empty provider name")
        if self.dimension <= 0:
            raise ValueError("Invalid embedding dimension")
            
        self._validate_impl()
        
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        pass
        
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Clean up implementation."""
        pass
        
    def _validate_impl(self) -> None:
        """Validate implementation."""
        pass
        
    @abstractmethod
    async def embed_text(
        self,
        text: Union[str, List[str]],
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text.
        
        Args:
            text: Text to embed (single string or list of strings)
            
        Returns:
            Embeddings (single vector or list of vectors)
        """
        raise NotImplementedError
    
    @abstractmethod
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
    async def _embed_impl(self, text: str) -> Dict[str, Any]:
        """Implementation-specific text embedding.
        
        Args:
            text: Input text.
            
        Returns:
            Embedding vectors.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        raise NotImplementedError
    
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