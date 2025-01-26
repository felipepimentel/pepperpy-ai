"""Milvus vector store provider implementation."""
from typing import Any, Dict, List, Optional, Tuple
import uuid

from pymilvus import Collection, connections, utility

from ...base import VectorStoreProvider
from ....core.utils.helpers import DataUtils

class SearchManager:
    """Manages search operations for Milvus."""
    
    @staticmethod
    def search(
        collection: Collection,
        vectors: List[List[float]],
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute search operation."""
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        expr = None
        if metadata_filter:
            expr = " and ".join([f"{k} == '{v}'" for k, v in metadata_filter.items()])
        
        results = collection.search(
            data=vectors,
            anns_field="vector",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=["id", "metadata"]
        )
        
        return SearchManager._process_results(results)
    
    @staticmethod
    def _process_results(results: Any) -> List[Dict[str, Any]]:
        """Process search results."""
        processed = []
        for hits in results:
            for hit in hits:
                processed.append({
                    "id": str(hit.entity.get("id")),
                    "metadata": DataUtils.parse_json(hit.entity.get("metadata", "{}")),
                    "score": hit.score
                })
        return processed

class MilvusConnection:
    """Manages Milvus connection."""
    
    @staticmethod
    def connect(host: str, port: int) -> None:
        """Connect to Milvus."""
        connections.connect(
            alias="default",
            host=host,
            port=port
        )
    
    @staticmethod
    def disconnect() -> None:
        """Disconnect from Milvus."""
        connections.disconnect("default")

class SchemaManager:
    """Manages Milvus schema."""
    
    @staticmethod
    def create_schema(dim: int) -> List[Dict[str, Any]]:
        """Create collection schema."""
        return [
            {"name": "id", "dtype": str, "is_primary": True},
            {"name": "vector", "dtype": List[float], "dim": dim},
            {"name": "metadata", "dtype": str}
        ]

class CollectionManager:
    """Manages Milvus collections."""
    
    @staticmethod
    def get_or_create(name: str, dim: int) -> Collection:
        """Get or create a collection."""
        if utility.has_collection(name):
            return Collection(name)
        
        fields = SchemaManager.create_schema(dim)
        collection = Collection(
            name=name,
            schema=fields
        )
        collection.create_index(
            field_name="vector",
            index_params={"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 1024}}
        )
        return collection

class EntityManager:
    """Manages Milvus entities."""
    
    @staticmethod
    def create_entities(
        vectors: List[List[float]],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[str], List[str], List[str]]:
        """Create entities for insertion."""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in vectors]
        if metadata is None:
            metadata = [{} for _ in vectors]
            
        metadata_strs = [DataUtils.to_json(m) for m in metadata]
        return ids, metadata_strs, ids

class MilvusProvider(VectorStoreProvider):
    """Milvus vector store provider."""
    
    def __init__(self, collection_name: str, dimension: int):
        """Initialize provider."""
        self.collection_name = collection_name
        self.dimension = dimension
        self.collection = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider."""
        host = config.get("host", "localhost")
        port = config.get("port", 19530)
        MilvusConnection.connect(host, port)
        self.collection = CollectionManager.get_or_create(self.collection_name, self.dimension)
        self.collection.load()
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.collection:
            self.collection.release()
        MilvusConnection.disconnect()
    
    async def add(
        self,
        vectors: List[List[float]],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to the store."""
        entity_ids, metadata_strs, return_ids = EntityManager.create_entities(vectors, ids, metadata)
        
        self.collection.insert([
            entity_ids,
            vectors,
            metadata_strs
        ])
        return return_ids
    
    async def search(
        self,
        vectors: List[List[float]],
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        return SearchManager.search(self.collection, vectors, limit, metadata_filter) 