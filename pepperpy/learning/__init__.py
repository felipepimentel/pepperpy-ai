"""Learning module for managing AI learning capabilities.

This module provides functionality for embedding generation, RAG workflows,
and fine-tuning strategies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Union, cast, overload

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle

from .providers.openai import OpenAIEmbeddingModel
from .strategies.rag import RAGStrategy
from .strategies.fine_tuning import FineTuningStrategy


class EmbeddingError(PepperpyError):
    """Embedding model error."""
    pass


class EmbeddingModel(Lifecycle, ABC):
    """Base class for embedding models."""
    
    def __init__(
        self,
        name: str,
        dimension: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize embedding model.
        
        Args:
            name: Model name
            dimension: Embedding dimension
            config: Optional model configuration
        """
        super().__init__()
        self.name = name
        self._dimension = dimension
        self._config = config or {}
        
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get model configuration."""
        return self._config
        
    @abstractmethod
    @overload
    async def embed(
        self,
        texts: str,
        batch_size: Optional[int] = None,
    ) -> List[float]:
        ...
        
    @abstractmethod
    @overload
    async def embed(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> List[List[float]]:
        ...
        
    @abstractmethod
    async def embed(
        self,
        texts: Union[str, List[str]],
        batch_size: Optional[int] = None,
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for texts.
        
        Args:
            texts: Text or list of texts to embed
            batch_size: Optional batch size for processing
            
        Returns:
            Single embedding vector or list of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass
        
    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Query embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        embeddings = await self.embed(text)
        if isinstance(embeddings, list) and all(isinstance(x, float) for x in embeddings):
            return cast(List[float], embeddings)
        raise EmbeddingError("Invalid query embedding format")
        
    async def embed_documents(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> List[List[float]]:
        """Generate embeddings for documents.
        
        Args:
            texts: List of document texts to embed
            batch_size: Optional batch size for processing
            
        Returns:
            List of document embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        embeddings = await self.embed(texts, batch_size)
        if isinstance(embeddings, list) and all(isinstance(x, list) for x in embeddings):
            return cast(List[List[float]], embeddings)
        raise EmbeddingError("Invalid document embeddings format")
        
    def validate(self) -> None:
        """Validate model state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Model name cannot be empty")
            
        if self._dimension <= 0:
            raise ValueError("Embedding dimension must be positive")


__all__ = [
    "EmbeddingError",
    "EmbeddingModel",
    "OpenAIEmbeddingModel",
    "RAGStrategy",
    "FineTuningStrategy",
] 