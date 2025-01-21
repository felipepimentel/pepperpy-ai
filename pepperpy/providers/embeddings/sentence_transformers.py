"""SentenceTransformers embedding provider implementation."""

from typing import Dict, Any, List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm
import torch
from scipy.spatial.distance import cosine, euclidean

from .base import BaseEmbeddingProvider

@BaseEmbeddingProvider.register("sentence_transformers")
class SentenceTransformersProvider(BaseEmbeddingProvider):
    """SentenceTransformers embedding provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider.
        
        Args:
            config: Configuration dictionary for the provider.
        """
        super().__init__(config)
        self.model: Optional[SentenceTransformer] = None
        self.model_name = config.get("model_name", "all-MiniLM-L6-v2")
        self.device = config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        self.normalize_embeddings = config.get("normalize_embeddings", True)
    
    async def initialize(self) -> None:
        """Initialize provider resources.
        
        Raises:
            ValueError: If initialization fails.
        """
        try:
            model = SentenceTransformer(self.model_name, device=self.device)
            self.dimension = model.get_sentence_embedding_dimension()
            self.model = model
        except Exception as e:
            self.model = None
            self.dimension = None
            raise ValueError(f"Failed to initialize SentenceTransformers provider: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self.model is not None:
            self.model = None
            self.dimension = None
    
    async def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text.
        
        Args:
            text: Single text or list of texts to embed.
            
        Returns:
            Single embedding vector or list of embedding vectors.
            
        Raises:
            ValueError: If the provider is not initialized.
        """
        if self.model is None:
            raise ValueError("Provider not initialized")
            
        embeddings = self.model.encode(
            text,
            normalize_embeddings=self.normalize_embeddings
        )
        
        if isinstance(text, str):
            return embeddings.tolist()
        return [embedding.tolist() for embedding in embeddings]
    
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
        if self.model is None:
            raise ValueError("Provider not initialized")
            
        embeddings = []
        
        for i in tqdm(
            range(0, len(texts), batch_size),
            disable=not show_progress,
            desc="Generating embeddings"
        ):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(
                batch,
                normalize_embeddings=self.normalize_embeddings,
                batch_size=batch_size
            )
            embeddings.extend(batch_embeddings.tolist())
            
        return embeddings
    
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
        if self.model is None:
            raise ValueError("Provider not initialized")
            
        embeddings = await self.embed_text([text1, text2])
        
        if metric == "cosine":
            return 1 - cosine(embeddings[0], embeddings[1])
        elif metric == "dot":
            return float(np.dot(embeddings[0], embeddings[1]))
        elif metric == "euclidean":
            return 1 / (1 + euclidean(embeddings[0], embeddings[1]))
        else:
            raise ValueError(f"Invalid similarity metric: {metric}") 