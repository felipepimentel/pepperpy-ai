"""LanceDB vector database provider for RAG."""

import os
import uuid
from typing import Any, List, Optional, Sequence, Union

import lancedb
import pyarrow as pa

from pepperpy.core.base import ValidationError
from pepperpy.rag.base import Document, Query, RAGProvider, SearchResult


class LanceDBProvider(RAGProvider):
    """LanceDB vector database provider for RAG."""

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
def __init__(
        self,
        uri: Optional[str] = None,
        table_name: str = "pepperpy",
        dimension: int = 1536,  # Default for text-embedding-3-small
        **kwargs: Any,
    ) -> None:
        """Initialize LanceDB provider.

        Args:
            uri: URI to the database. If None, uses ~/.lancedb
            table_name: Name of the table to use
            dimension: Dimension of vectors (default 1536 for text-embedding-3-small)
            **kwargs: Additional configuration parameters
        """
        super().__init__()
        self.uri = uri or os.path.join(os.path.expanduser("~"), ".lancedb")
        self.table_name = table_name
        self.dimension = dimension
        self.kwargs = kwargs
        self._db = None
        self._table = None

    def _get_table(self) -> Any:
        """Get the table, raising an error if not initialized.

        Returns:
            The initialized table

        Raises:
            ValidationError: If table is not initialized
        """
        if self._table is None:
            raise ValidationError("Table not initialized")
        return self._table

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates the table if it doesn't exist.
        """
        # Create database directory if it doesn't exist
        os.makedirs(self.uri, exist_ok=True)

        # Connect to database
        self._db = lancedb.connect(self.uri)

        # Create schema for the table
        schema = pa.schema([
            ("id", pa.string()),
            ("text", pa.string()),
            ("metadata", pa.string()),  # JSON serialized
            ("vector", pa.list_(pa.float32(), self.dimension)),
        ])

        # Create or get table
        if self.table_name not in self._db.table_names():
            self._table = self._db.create_table(
                self.table_name,
                schema=schema,
                mode="create",
            )
        else:
            self._table = self._db.open_table(self.table_name)

        # Create vector index if it doesn't exist
        if not self._table.has_index():
            self._table.create_index(
                metric="cosine",
                **self.kwargs,
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._table = None
        if self._db is not None:
            self._db.close()
            self._db = None

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in LanceDB.

        Args:
            docs: Document or list of documents to store
        """
        if isinstance(docs, Document):
            docs = [docs]

        data = []
        for doc in docs:
            if "embeddings" not in doc.metadata:
                raise ValidationError("Document must have embeddings in metadata")

            doc_id = str(uuid.uuid4())
            data.append({
                "id": doc_id,
                "text": doc.text,
                "metadata": doc.metadata,
                "vector": doc.metadata["embeddings"],
            })

        self._get_table().add(data)

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

        results = (
            self._get_table()
            .search(query.embeddings)
            .limit(limit)
            .select(["id", "text", "metadata", "_distance"])
            .to_list()
        )

        search_results = []
        for hit in results:
            search_results.append(
                SearchResult(
                    id=hit["id"],
                    text=hit["text"],
                    metadata=hit["metadata"],
                    score=1.0
                    - float(hit["_distance"]),  # Convert distance to similarity
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
        results = (
            self._get_table()
            .filter(f"id = '{doc_id}'")
            .select(["text", "metadata"])
            .to_list()
        )

        if not results:
            return None

        result = results[0]
        return Document(
            text=result["text"],
            metadata=result["metadata"],
        )
