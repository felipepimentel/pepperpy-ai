"""Qdrant vector database provider for RAG."""

from typing import Any, Dict, List, Optional, Sequence, Union
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from pepperpy.core.base import ValidationError
from pepperpy.rag.base import Document, Query, RAGProvider, SearchResult

class QdrantProvider(RAGProvider):
    """Qdrant vector database provider for RAG."""

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    client: Optional[httpx.AsyncClient] = None
def __init__(
        self,
        collection_name: str = "pepperpy",
        host: Optional[str] = None,
        port: Optional[int] = 6333,
        grpc_port: Optional[int] = 6334,
        prefer_grpc: bool = False,
        https: Optional[bool] = None,
        api_key: Optional[str] = None,
        prefix: Optional[str] = None,
        timeout: Optional[float] = None,
        host_url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Qdrant provider.

        Args:
            collection_name: Name of the collection to use
            host: Qdrant server host
            port: REST port
            grpc_port: gRPC port
            prefer_grpc: Whether to prefer gRPC over REST
            https: Whether to use HTTPS
            api_key: API key for authentication
            prefix: URL prefix
            timeout: Request timeout in seconds
            host_url: Complete Qdrant server URL (overrides host/port)
            **kwargs: Additional client parameters
        """
        super().__init__()
        self.collection_name = collection_name
        self.vector_size = kwargs.pop("vector_size", 1536)  # Default for text-embedding-3-small
        
        # Initialize client
        self.client = QdrantClient(
            host=host,
            port=port,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
            https=https,
            api_key=api_key,
            prefix=prefix,
            timeout=timeout,
            host=host_url,
            **kwargs,
        )

    async def initialize(self) -> None:
        """Initialize the provider.
        
        Creates the collection if it doesn't exist.
        """
        # Check if collection exists
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if hasattr(self, "client"):
            self.client.close()

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in Qdrant.

        Args:
            docs: Document or list of documents to store
        """
        if isinstance(docs, Document):
            docs = [docs]

        points = []
        for doc in docs:
            if "embeddings" not in doc.metadata:
                raise ValidationError("Document must have embeddings in metadata")
            
            doc_id = str(uuid.uuid4())
            points.append(
                models.PointStruct(
                    id=doc_id,
                    vector=doc.metadata["embeddings"],
                    payload={
                        "text": doc.text,
                        "metadata": doc.metadata,
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    async def search(
        self,
        query: Union[str, Query],
        limit: int = 5,
        **kwargs: Any,
    ) -> Sequence[SearchResult]:
        """Search for relevant documents.

        Args:
            query: Search query text or Query object
            limit: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        if isinstance(query, str):
            query = Query(text=query)

        if not query.embeddings:
            raise ValidationError("Query must have embeddings")

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query.embeddings,
            limit=limit,
            **kwargs,
        )

        search_results = []
        for hit in results:
            search_results.append(
                SearchResult(
                    id=str(hit.id),
                    text=hit.payload["text"],
                    metadata=hit.payload["metadata"],
                    score=hit.score,
                )
            )

        return search_results

    async def get(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID.

        Args:
            doc_id: ID of the document to get

        Returns:
            The document if found, None otherwise
        """
        try:
            point = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[doc_id],
            )[0]
        except IndexError:
            return None

        return Document(
            text=point.payload["text"],
            metadata=point.payload["metadata"],
        ) 