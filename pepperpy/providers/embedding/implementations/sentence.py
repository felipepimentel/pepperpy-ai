"""Sentence Transformers embedding provider implementation."""
from typing import List

from sentence_transformers import SentenceTransformer

from ...base.provider import BaseProvider, ProviderConfig

class SentenceTransformerProvider(BaseProvider):
    """Provider for Sentence Transformers embeddings."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the Sentence Transformers provider."""
        super().__init__(config)
        self.model = None
        self.model_name = config.parameters.get("model", "all-MiniLM-L6-v2")
    
    async def initialize(self) -> None:
        """Initialize the model."""
        if not self._initialized:
            self.model = SentenceTransformer(self.model_name)
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.model = None
        self._initialized = False
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for the given texts."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist() 