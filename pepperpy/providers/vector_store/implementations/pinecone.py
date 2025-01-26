"""Pinecone vector store provider implementation."""
from typing import Any, Dict, List, Optional, Tuple
import uuid

from pinecone import Pinecone, Index

from ...base import VectorStoreProvider

class SearchManager:
    """Manages search operations for Pinecone."""
    
    @staticmethod
    def search(
        index: Index,
        vector: List[float],
        namespace: str,
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute search operation."""
        results = index.query(
            vector=vector,
            top_k=limit,
            namespace=namespace,
            filter=metadata_filter,
            include_metadata=True
        )
        return SearchManager._process_results(results)
    
    @staticmethod
    def _process_results(results: Any) -> List[Dict[str, Any]]:
        """Process search results."""
        processed = []
        for match in results.matches:
            processed.append({
                "id": str(match.id),
                "metadata": match.metadata or {},
                "score": float(match.score)
            })
        return processed

class PineconeConnection:
    """Manages Pinecone connection."""
    
    @staticmethod
    def create_client(api_key: str) -> Pinecone:
        """Create Pinecone client."""
        return Pinecone(api_key=api_key)

class IndexManager:
    """Manages Pinecone indexes."""
    
    @staticmethod
    def get_or_create(
        client: Pinecone,
        name: str,
        dimension: int = 1536,
        metric: str = "cosine"
    ) -> Index:
        """Get or create an index."""
        if name not in client.list_indexes().names():
            client.create_index(
                name=name,
                dimension=dimension,
                metric=metric
            )
        return client.Index(name)

class EntityManager:
    """Manages Pinecone entities."""
    
    @staticmethod
    def create_entities(
        vectors: List[List[float]],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Create entities for upsert."""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in vectors]
        if metadata is None:
            metadata = [{} for _ in vectors]
        
        return [
            {"id": id, "values": vector, "metadata": meta}
            for id, vector, meta in zip(ids, vectors, metadata)
        ]
    
    @staticmethod
    def batch_upsert(
        index: Index,
        entities: List[Dict[str, Any]],
        namespace: str,
        batch_size: int = 100
    ) -> None:
        """Upsert entities in batches."""
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            index.upsert(vectors=batch, namespace=namespace)

class PineconeProvider(VectorStoreProvider):
    """Pinecone vector store provider."""
    
    def __init__(self, index_name: str, namespace: str = "default"):
        """Initialize provider."""
        self.index_name = index_name
        self.namespace = namespace
        self.client = None
        self.index = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider."""
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("Pinecone API key is required")
        
        environment = config.get("environment")
        if not environment:
            raise ValueError("Pinecone environment is required")
        
        dimension = config.get("dim", 1536)  # Default for OpenAI embeddings
        metric = config.get("metric", "cosine")
        
        self.client = PineconeConnection.create_client(api_key)
        self.index = IndexManager.get_or_create(
            self.client,
            self.index_name,
            dimension,
            metric
        )
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.index = None
        self.client = None
    
    async def add(
        self,
        vectors: List[List[float]],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to the store."""
        entities = EntityManager.create_entities(vectors, ids, metadata)
        EntityManager.batch_upsert(self.index, entities, self.namespace)
        return [entity["id"] for entity in entities]
    
    async def search(
        self,
        vectors: List[List[float]],
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        # Pinecone only supports single vector search
        vector = vectors[0] if vectors else []
        return SearchManager.search(
            self.index,
            vector,
            self.namespace,
            limit,
            metadata_filter
        ) 