"""Milvus vector store provider implementation."""
from typing import Any, Dict, List, Optional, Tuple

from pymilvus import Collection, connections, utility

from ...base.provider import BaseProvider, ProviderConfig

class MilvusProvider(BaseProvider):
    """Provider for Milvus vector store."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the Milvus provider."""
        super().__init__(config)
        self.collection = None
        self.collection_name = config.parameters.get("collection_name", "pepperpy_vectors")
        self.dim = config.parameters.get("dim", 1536)  # Default for OpenAI embeddings
    
    async def initialize(self) -> None:
        """Initialize the Milvus connection."""
        if not self._initialized:
            await self._connect()
            await self._setup_collection()
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.collection:
            self.collection.release()
            connections.disconnect("default")
            self._initialized = False
    
    async def _connect(self) -> None:
        """Connect to Milvus."""
        host = self.config.parameters.get("host", "localhost")
        port = self.config.parameters.get("port", 19530)
        
        connections.connect(
            alias="default",
            host=host,
            port=port
        )
    
    async def _setup_collection(self) -> None:
        """Setup Milvus collection."""
        if not utility.has_collection(self.collection_name):
            await self._create_collection()
        
        self.collection = Collection(self.collection_name)
        self.collection.load()
    
    async def _create_collection(self) -> None:
        """Create Milvus collection."""
        fields = [
            {
                "name": "id",
                "dtype": "VARCHAR(128)",
                "is_primary": True,
            },
            {
                "name": "vector",
                "dtype": "FLOAT_VECTOR",
                "dim": self.dim
            },
            {
                "name": "metadata",
                "dtype": "JSON",
                "description": "Additional metadata"
            }
        ]
        
        schema = {
            "fields": fields,
            "description": "Pepperpy vector store"
        }
        
        Collection(
            name=self.collection_name,
            schema=schema,
            using="default"
        )
    
    async def add(
        self,
        vectors: List[List[float]],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to Milvus."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        # Generate IDs if not provided
        if ids is None:
            ids = [utility.gen_unique_id() for _ in vectors]
        
        # Use empty metadata if not provided
        if metadata is None:
            metadata = [{} for _ in vectors]
        
        entities = [
            {"id": id, "vector": vector, "metadata": meta}
            for id, vector, meta in zip(ids, vectors, metadata)
        ]
        
        self.collection.insert(entities)
        return ids
    
    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors in Milvus."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        
        expr = self._build_filter_expr(metadata_filter) if metadata_filter else None
        
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=["metadata"]
        )
        
        return self._process_search_results(results)
    
    def _build_filter_expr(self, metadata_filter: Dict[str, Any]) -> str:
        """Build Milvus filter expression."""
        conditions = []
        for key, value in metadata_filter.items():
            conditions.append(f'metadata["{key}"] == "{value}"')
        return " && ".join(conditions)
    
    def _process_search_results(
        self,
        results: Any
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Process Milvus search results."""
        matches = []
        for hits in results:
            for hit in hits:
                matches.append((
                    str(hit.id),
                    float(hit.distance),
                    hit.entity.get("metadata", {})
                ))
        return matches 