"""Vector embeddings implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, TypeVar

import numpy as np
from numpy.typing import NDArray

from ...common.errors import PepperpyError
from ...core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class EmbeddingError(PepperpyError):
    """Embedding error."""
    pass


class EmbeddingModel(Protocol):
    """Embedding model protocol."""
    
    async def embed(self, text: str) -> NDArray[np.float32]:
        """Embed text into vector space.
        
        Args:
            text: Text to embed
            
        Returns:
            Text embedding
            
        Raises:
            EmbeddingError: If text cannot be embedded
        """
        ...


M = TypeVar("M", bound=EmbeddingModel)


class EmbeddingManager(Lifecycle):
    """Embedding manager implementation."""
    
    def __init__(
        self,
        name: str,
        model: EmbeddingModel,
        dimension: int,
        normalize: bool = True,
        cache_size: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize embedding manager.
        
        Args:
            name: Manager name
            model: Embedding model
            dimension: Embedding dimension
            normalize: Whether to normalize embeddings (default: True)
            cache_size: Optional cache size
            config: Optional manager configuration
        """
        super().__init__(name)
        self._model = model
        self._dimension = dimension
        self._normalize = normalize
        self._cache_size = cache_size
        self._config = config or {}
        self._cache: Dict[str, NDArray[np.float32]] = {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return manager configuration."""
        return self._config
        
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension
        
    async def _initialize(self) -> None:
        """Initialize manager."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up manager."""
        self._cache.clear()
        
    async def get_embedding(self, text: str) -> NDArray[np.float32]:
        """Get text embedding.
        
        Args:
            text: Text to embed
            
        Returns:
            Text embedding
            
        Raises:
            EmbeddingError: If text cannot be embedded
        """
        try:
            # Check cache
            if text in self._cache:
                return self._cache[text]
                
            # Get embedding
            embedding = await self._model.embed(text)
            
            # Validate dimension
            if embedding.shape != (self._dimension,):
                raise EmbeddingError(
                    f"Expected embedding dimension {self._dimension}, "
                    f"got {embedding.shape[0]}"
                )
                
            # Normalize if needed
            if self._normalize:
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding /= norm
                    
            # Update cache
            if self._cache_size is not None:
                if len(self._cache) >= self._cache_size:
                    self._cache.pop(next(iter(self._cache)))
                self._cache[text] = embedding
                
            return embedding
            
        except Exception as e:
            raise EmbeddingError(f"Failed to get embedding: {e}") from e
            
    async def get_embeddings(self, texts: List[str]) -> NDArray[np.float32]:
        """Get text embeddings.
        
        Args:
            texts: Texts to embed
            
        Returns:
            Text embeddings
            
        Raises:
            EmbeddingError: If texts cannot be embedded
        """
        try:
            # Get embeddings
            embeddings = []
            for text in texts:
                embedding = await self.get_embedding(text)
                embeddings.append(embedding)
                
            return np.array(embeddings)
            
        except Exception as e:
            raise EmbeddingError(f"Failed to get embeddings: {e}") from e
            
    def validate(self) -> None:
        """Validate manager state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Manager name cannot be empty")
            
        if not self._model:
            raise ValueError("Embedding model not provided")
            
        if self._dimension <= 0:
            raise ValueError("Embedding dimension must be positive")
            
        if self._cache_size is not None and self._cache_size <= 0:
            raise ValueError("Cache size must be positive")
