"""Pinecone vector store provider implementation."""
from typing import Any, Dict, List, Optional, Tuple

from pinecone import Pinecone, Index

from ...base.provider import BaseProvider, ProviderConfig

class PineconeProvider(BaseProvider):
    """Provider for Pinecone vector store."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the Pinecone provider."""
        super().__init__(config)
        self.client = None
        self.index = None
        self.index_name = config.parameters.get("index_name", "pepperpy-vectors")
        self.namespace = config.parameters.get("namespace", "default")
    
    async def initialize(self) -> None:
        """Initialize the Pinecone client."""
        if not self._initialized:
            await self._validate_config()
            await self._setup_client()
            await self._setup_index()
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.index = None
        self.client = None
        self._initialized = False
    
    async def _validate_config(self) -> None:
        """Validate configuration."""
        api_key = self.config.parameters.get("api_key")
        if not api_key:
            raise ValueError("Pinecone API key is required")
        
        environment = self.config.parameters.get("environment")
        if not environment:
            raise ValueError("Pinecone environment is required")
    
    async def _setup_client(self) -> None:
        """Setup Pinecone client."""
        self.client = Pinecone(api_key=self.config.parameters["api_key"])
    
    async def _setup_index(self) -> None:
        """Setup Pinecone index."""
        if self.index_name not in self.client.list_indexes().names():
            await self._create_index()
        
        self.index = self.client.Index(self.index_name)
    
    async def _create_index(self) -> None:
        """Create Pinecone index."""
        self.client.create_index(
            name=self.index_name,
            dimension=self.config.parameters.get("dim", 1536),  # Default for OpenAI
            metric=self.config.parameters.get("metric", "cosine")
        )
    
    async def add(
        self,
        vectors: List[List[float]],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to Pinecone."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        # Generate IDs if not provided
        if ids is None:
            ids = [f"vec_{i}" for i in range(len(vectors))]
        
        # Use empty metadata if not provided
        if metadata is None:
            metadata = [{} for _ in vectors]
        
        # Prepare vectors for upsert
        items = [
            (id, vector, meta)
            for id, vector, meta in zip(ids, vectors, metadata)
        ]
        
        await self._batch_upsert(items)
        return ids
    
    async def _batch_upsert(
        self,
        items: List[Tuple[str, List[float], Dict[str, Any]]]
    ) -> None:
        """Upsert vectors in batches."""
        batch_size = 100  # Pinecone's limit
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            self.index.upsert(
                vectors=[
                    {
                        "id": id,
                        "values": vector,
                        "metadata": meta
                    }
                    for id, vector, meta in batch
                ],
                namespace=self.namespace
            )
    
    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors in Pinecone."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        results = self.index.query(
            vector=query_vector,
            top_k=limit,
            namespace=self.namespace,
            filter=metadata_filter,
            include_metadata=True
        )
        
        return self._process_results(results)
    
    def _process_results(
        self,
        results: Any
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Process search results."""
        matches = []
        for match in results.matches:
            matches.append((
                str(match.id),
                float(match.score),
                match.metadata or {}
            ))
        return matches 