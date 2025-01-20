"""Base embedding model classes for Pepperpy."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import numpy as np
from numpy.typing import NDArray

from ....common.errors import ModelError
from ....core.lifecycle import Lifecycle


class EmbeddingModel(Lifecycle, ABC):
    """Base class for embedding models."""
    
    def __init__(
        self,
        name: str,
        model: str,
        dimension: int,
        **kwargs: Any,
    ) -> None:
        """Initialize embedding model.
        
        Args:
            name: Model name
            model: Model identifier
            dimension: Embedding dimension
            **kwargs: Additional model parameters
        """
        super().__init__(name)
        self._model = model
        self._dimension = dimension
        self._kwargs = kwargs
        self._initialized = False
        
    @property
    def model(self) -> str:
        """Get model identifier."""
        return self._model
        
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
        
    @property
    def is_initialized(self) -> bool:
        """Check if model is initialized."""
        return self._initialized
        
    async def _initialize(self) -> None:
        """Initialize model."""
        self._initialized = True
        
    async def _cleanup(self) -> None:
        """Cleanup model."""
        self._initialized = False
        
    async def embed(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
    ) -> NDArray[np.float32]:
        """Generate embeddings for input texts.
        
        Args:
            texts: Input text or list of texts
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings with shape (N, dimension)
            
        Raises:
            ModelError: If model is not initialized
        """
        if not self.is_initialized:
            raise ModelError("Model not initialized")
            
        # Convert single text to list
        if isinstance(texts, str):
            texts = [texts]
            
        # Process texts in batches
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._embed(batch)
            embeddings.append(batch_embeddings)
            
        # Concatenate batches
        return np.concatenate(embeddings, axis=0)
        
    @abstractmethod
    async def _embed(self, texts: List[str]) -> NDArray[np.float32]:
        """Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            Array of embeddings with shape (N, dimension)
        """
        pass 