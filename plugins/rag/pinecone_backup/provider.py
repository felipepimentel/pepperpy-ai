"""Pinecone vector database provider for RAG."""

import uuid
from typing import Any, List, Optional, Sequence, Union

import pinecone

from pepperpy.core.base import ValidationError
from pepperpy.rag.base import Document, Query, RAGProvider, SearchResult


class PineconeProvider(RAGProvider):
    """Pinecone vector database provider for RAG."""

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
def __init__(
        self,
        index_name: str,
        api_key: str,
        environment: str = "gcp-starter",
        namespace: Optional[str] = None,
        dimension: int = 1536,  # Default for text-embedding-3-small
        metric: str = "cosine",
        **kwargs: Any,
    ) -> None:
        """Initialize Pinecone provider.

        Args:
            index_name: Name of the Pinecone index
            api_key: Pinecone API key
            environment: Pinecone environment
            namespace: Optional namespace for the index
            dimension: Dimension of vectors (default 1536 for text-embedding-3-small)
            metric: Distance metric to use (default: cosine)
            **kwargs: Additional configuration parameters
        """
        super().__init__()
        self.index_name = index_name
        self.namespace = namespace
        self.dimension = dimension
        self.metric = metric
        self.api_key = api_key
        self.environment = environment
        self.kwargs = kwargs

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates the index if it doesn't exist.
        """
        # Initialize Pinecone
        pinecone.init(
            api_key=self.api_key,
            environment=self.environment,
        )

        # Check if index exists
        if self.index_name not in pinecone.list_indexes():
            # Create new index
            pinecone.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                **self.kwargs,
            )

        self.index = pinecone.Index(self.index_name)

    async def cleanup(self) -> None:
        """Clean up resources."""
        if hasattr(self, "index"):
            self.index.close()

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in Pinecone.

        Args:
            docs: Document or list of documents to store
        """
        if isinstance(docs, Document):
            docs = [docs]

        vectors = []
        for doc in docs:
            if "embeddings" not in doc.metadata:
                raise ValidationError("Document must have embeddings in metadata")

            doc_id = str(uuid.uuid4())
            vectors.append((
                doc_id,
                doc.metadata["embeddings"],
                {
                    "text": doc.text,
                    "metadata": doc.metadata,
                },
            ))

        self.index.upsert(
            vectors=vectors,
            namespace=self.namespace,
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

        results = self.index.query(
            vector=query.embeddings,
            top_k=limit,
            namespace=self.namespace,
            include_metadata=True,
            **kwargs,
        )

        search_results = []
        for match in results.matches:
            search_results.append(
                SearchResult(
                    id=match.id,
                    text=match.metadata["text"],
                    metadata=match.metadata["metadata"],
                    score=match.score,
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
            vector = self.index.fetch(
                ids=[doc_id],
                namespace=self.namespace,
            )[doc_id]
        except KeyError:
            return None

        return Document(
            text=vector.metadata["text"],
            metadata=vector.metadata["metadata"],
        )
