"""OpenAI embedding model implementation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from openai import AsyncOpenAI

from pepperpy.core.utils.errors import PepperpyError
from .base import EmbeddingModel, EmbeddingError


logger = logging.getLogger(__name__)


class OpenAIEmbeddingModel(EmbeddingModel):
    """OpenAI embedding model implementation."""
    
    def __init__(
        self,
        name: str,
        model: str = "text-embedding-ada-002",
        api_key: Optional[str] = None,
        batch_size: int = 100,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize OpenAI embedding model.
        
        Args:
            name: Model name
            model: OpenAI model name
            api_key: Optional OpenAI API key
            batch_size: Maximum batch size for API calls
            config: Optional model configuration
        """
        super().__init__(name, dimension=1536, config=config)
        self._model = model
        self._api_key = api_key
        self._batch_size = batch_size
        self._client: Optional[AsyncOpenAI] = None
        
    async def initialize(self) -> None:
        """Initialize model."""
        self._client = AsyncOpenAI(api_key=self._api_key) if self._api_key else AsyncOpenAI()
            
    async def cleanup(self) -> None:
        """Clean up model."""
        if self._client:
            await self._client.close()
            self._client = None
        
    async def embed(
        self,
        texts: Union[str, List[str]],
        batch_size: Optional[int] = None,
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for texts.
        
        Args:
            texts: Text or list of texts to embed
            batch_size: Optional batch size for API calls
            
        Returns:
            Single embedding vector or list of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        if isinstance(texts, str):
            return await self._embed_single(texts)
            
        batch_size = batch_size or self._batch_size
        return await self._embed_batch(texts, batch_size)
        
    async def _embed_single(self, text: str) -> List[float]:
        """Generate embedding for single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not self._client:
            raise EmbeddingError("OpenAI client not initialized")
            
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=text,
            )
            return response.data[0].embedding
            
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embedding: {e}")
            
    async def _embed_batch(
        self,
        texts: List[str],
        batch_size: int,
    ) -> List[List[float]]:
        """Generate embeddings for batch of texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Maximum batch size for API calls
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not self._client:
            raise EmbeddingError("OpenAI client not initialized")
            
        try:
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=batch,
                )
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                
            return embeddings
            
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}")
            
    def validate(self) -> None:
        """Validate model state."""
        super().validate()
        
        if not self._model:
            raise ValueError("OpenAI model name cannot be empty")
            
        if self._batch_size <= 0:
            raise ValueError("Batch size must be positive") 