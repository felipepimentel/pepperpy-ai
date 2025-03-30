"""Epsilla vector database provider for RAG."""

import uuid
from typing import Any, List, Optional, Sequence, Union

from epsilla import Client

from pepperpy.core.base import ValidationError
from pepperpy.rag.base import Document, Query, RAGProvider, SearchResult


class EpsillaProvider(RAGProvider):
    """Epsilla vector database provider for RAG."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8888,
        db_name: str = "pepperpy",
        table_name: str = "documents",
        dimension: int = 1536,  # Default for text-embedding-3-small
        **kwargs: Any,
    ) -> None:
        """Initialize Epsilla provider.

        Args:
            host: Epsilla server host
            port: Epsilla server port
            db_name: Name of the database to use
            table_name: Name of the table to use
            dimension: Dimension of vectors (default 1536 for text-embedding-3-small)
            **kwargs: Additional configuration parameters
        """
        super().__init__()
        self.host = host
        self.port = port
        self.db_name = db_name
        self.table_name = table_name
        self.dimension = dimension
        self.kwargs = kwargs
        self._client: Optional[Client] = None
        self._db = None

    def _get_client(self) -> Client:
        """Get the client, raising an error if not initialized.

        Returns:
            The initialized client

        Raises:
            ValidationError: If client is not initialized
        """
        if self._client is None:
            raise ValidationError("Client not initialized")
        return self._client

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates the database and table if they don't exist.
        """
        # Connect to Epsilla
        client = Client(f"http://{self.host}:{self.port}")

        # Create or use database
        client.create_database(self.db_name)
        client.use_database(self.db_name)

        # Create table if it doesn't exist
        try:
            client.create_table(
                name=self.table_name,
                fields=[
                    {"name": "id", "type": "string", "primary": True},
                    {"name": "text", "type": "string"},
                    {"name": "metadata", "type": "string"},  # JSON serialized
                    {
                        "name": "vector",
                        "type": "vector",
                        "dimension": self.dimension,
                        "metric": "cosine",
                    },
                ],
            )
        except Exception:
            # Table already exists
            pass

        self._client = client

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._client is not None:
            self._client.close()
            self._client = None

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in Epsilla.

        Args:
            docs: Document or list of documents to store
        """
        if isinstance(docs, Document):
            docs = [docs]

        records = []
        for doc in docs:
            if "embeddings" not in doc.metadata:
                raise ValidationError("Document must have embeddings in metadata")

            doc_id = str(uuid.uuid4())
            records.append({
                "id": doc_id,
                "text": doc.text,
                "metadata": doc.metadata,
                "vector": doc.metadata["embeddings"],
            })

        self._get_client().insert(
            table_name=self.table_name,
            records=records,
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

        results = self._get_client().query(
            table_name=self.table_name,
            query_vector=query.embeddings,
            limit=limit,
            **kwargs,
        )

        search_results = []
        for hit in results:
            search_results.append(
                SearchResult(
                    id=hit["id"],
                    text=hit["text"],
                    metadata=hit["metadata"],
                    score=hit["score"],
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
        results = self._get_client().get(
            table_name=self.table_name,
            ids=[doc_id],
        )

        if not results:
            return None

        result = results[0]
        return Document(
            text=result["text"],
            metadata=result["metadata"],
        )
