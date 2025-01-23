"""Qdrant vector store provider implementation."""

from typing import Dict, Any, List, Optional
import uuid
import asyncio
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from .base import BaseVectorStoreProvider

@BaseVectorStoreProvider.register("qdrant")
class QdrantVectorStore(BaseVectorStoreProvider):
    """Qdrant vector store provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider.
        
        Args:
            config: Configuration dictionary for the provider.
        """
        super().__init__(config)
        self.client: Optional[QdrantClient] = None
        self.collection_name = config.get("collection_name", "default")
        self.dimension = config.get("dimension", 768)  # Default for many embedding models
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 6333)
        self.grpc_port = config.get("grpc_port", 6334)
        self.prefer_grpc = config.get("prefer_grpc", False)
        self.api_key = config.get("api_key")
        self.https = config.get("https", False)
    
    async def initialize(self) -> None:
        """Initialize provider resources.
        
        Raises:
            ValueError: If initialization fails.
        """
        try:
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                grpc_port=self.grpc_port,
                prefer_grpc=self.prefer_grpc,
                api_key=self.api_key,
                https=self.https
            )
            
            if self.client is None:
                raise ValueError("Failed to initialize Qdrant client")
            
            # Check if collection exists
            try:
                self.client.get_collection(self.collection_name)
            except UnexpectedResponse:
                # Create collection if it doesn't exist
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.dimension,
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            self.client = None
            raise ValueError(f"Failed to initialize Qdrant provider: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self.client is not None:
            self.client.close()
            self.client = None
    
    async def add_vectors(
        self, 
        vectors: List[List[float]], 
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to the store.
        
        Args:
            vectors: List of vectors to add.
            metadata: Optional metadata for each vector.
            
        Returns:
            List of IDs for the added vectors.
            
        Raises:
            ValueError: If the client is not initialized.
        """
        if not vectors:
            return []
            
        if self.client is None:
            raise ValueError("Client not initialized")
            
        points = []
        ids = []
        
        for i, vector in enumerate(vectors):
            id = str(uuid.uuid4())
            ids.append(id)
            
            point = models.PointStruct(
                id=id,
                vector=vector,
                payload=metadata[i] if metadata and i < len(metadata) else {}
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return ids
    
    async def search(
        self, 
        query_vector: List[float], 
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Vector to search for.
            k: Number of results to return.
            filter_metadata: Optional metadata filters.
            
        Returns:
            List of results with their metadata and scores.
            
        Raises:
            ValueError: If the client is not initialized.
        """
        if self.client is None:
            raise ValueError("Client not initialized")
            
        # Convert filter_metadata to Qdrant filter format
        filter_condition = None
        if filter_metadata:
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
            filter_condition = models.Filter(
                must=conditions
            )
        
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=k,
            query_filter=filter_condition
        )
        
        return [
            {
                "id": str(point.id),
                "score": float(point.score),
                "metadata": point.payload
            }
            for point in search_result
        ]
    
    async def delete(self, ids: List[str]) -> bool:
        """Delete vectors from the store.
        
        Args:
            ids: List of vector IDs to delete.
            
        Returns:
            True if successful, False otherwise.
            
        Raises:
            ValueError: If the client is not initialized.
        """
        if self.client is None:
            raise ValueError("Client not initialized")
            
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=ids
                )
            )
            return True
        except Exception:
            return False
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a vector by its ID.
        
        Args:
            id: Vector ID.
            
        Returns:
            Vector data with metadata if found, None otherwise.
            
        Raises:
            ValueError: If the client is not initialized.
        """
        if self.client is None:
            raise ValueError("Client not initialized")
            
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[id]
            )
            
            if not points:
                return None
                
            point = points[0]
            return {
                "id": str(point.id),
                "vector": point.vector,
                "metadata": point.payload
            }
        except Exception:
            return None
    
    async def update_metadata(self, id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a vector.
        
        Args:
            id: Vector ID.
            metadata: New metadata.
            
        Returns:
            True if successful, False otherwise.
            
        Raises:
            ValueError: If the client is not initialized.
        """
        if self.client is None:
            raise ValueError("Client not initialized")
            
        try:
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=metadata,
                points=[id]
            )
            return True
        except Exception:
            return False 