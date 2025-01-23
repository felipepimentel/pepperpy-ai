"""OpenAI embedding provider implementation."""

from typing import Dict, Any, List, Union, Optional
import numpy as np
import aiohttp
from tqdm.auto import tqdm
from scipy.spatial.distance import cosine, euclidean

from .base import BaseEmbeddingProvider

@BaseEmbeddingProvider.register("openai")
class OpenAIProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider.
        
        Args:
            config: Configuration dictionary for the provider.
        """
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key = config.get("api_key")
        self.model_name = config.get("model_name", "text-embedding-ada-002")
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Model dimensions
        self.model_dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072
        }
    
    async def initialize(self) -> None:
        """Initialize provider resources.
        
        Raises:
            ValueError: If initialization fails.
        """
        try:
            if not self.api_key:
                raise ValueError("API key is required")
                
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                raise_for_status=True
            )
            
            self.dimension = self.model_dimensions.get(self.model_name)
            if self.dimension is None:
                raise ValueError(f"Unknown model: {self.model_name}")
                
        except Exception as e:
            self.session = None
            self.dimension = None
            raise ValueError(f"Failed to initialize OpenAI provider: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self.session is not None:
            await self.session.close()
            self.session = None
            self.dimension = None
    
    async def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text.
        
        Args:
            text: Single text or list of texts to embed.
            
        Returns:
            Single embedding vector or list of embedding vectors.
            
        Raises:
            ValueError: If the provider is not initialized.
            aiohttp.ClientError: If the API request fails.
        """
        if self.session is None:
            raise ValueError("Provider not initialized")
            
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        data = {
            "model": self.model_name,
            "input": texts
        }
        
        async with self.session.post(f"{self.base_url}/embeddings", json=data) as response:
            result = await response.json()
            embeddings = [item["embedding"] for item in result["data"]]
            
        return embeddings[0] if is_single else embeddings
    
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
            aiohttp.ClientError: If the API request fails.
        """
        if self.session is None:
            raise ValueError("Provider not initialized")
            
        embeddings = []
        
        for i in tqdm(
            range(0, len(texts), batch_size),
            disable=not show_progress,
            desc="Generating embeddings"
        ):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.embed_text(batch)
            embeddings.extend(batch_embeddings)
            
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
            aiohttp.ClientError: If the API request fails.
        """
        if self.session is None:
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