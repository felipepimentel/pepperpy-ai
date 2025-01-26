"""OpenAI embedding provider implementation."""
from typing import Any, Dict, List

from openai import AsyncOpenAI

from ...base.provider import BaseProvider, ProviderConfig

class OpenAIEmbeddingProvider(BaseProvider):
    """Provider for OpenAI embeddings."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the OpenAI embedding provider."""
        super().__init__(config)
        self.client = None
        self.model = config.parameters.get("model", "text-embedding-3-small")
    
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self._initialized:
            api_key = self.config.parameters.get("api_key")
            if not api_key:
                raise ValueError("OpenAI API key is required")
            
            self.client = AsyncOpenAI(api_key=api_key)
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.client:
            await self.client.close()
            self._initialized = False
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for the given texts."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        
        return [data.embedding for data in response.data] 