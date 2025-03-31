"""HyperDB vector database provider for RAG."""

import os
import uuid
from typing import Any, List, Optional, Sequence, Union

from hyperdb import HyperDB

from pepperpy.core.base import ValidationError
from pepperpy.rag.base import Document, Query, RAGProvider, SearchResult


class HyperDBProvider(RAGProvider):
    """HyperDB vector database provider for RAG."""

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
def __init__(
        self,
        persist_directory: Optional[str] = None,
        dimension: int = 1536,  # Default for text-embedding-3-small
        metric: str = "cosine",
        **kwargs: Any,
    ) -> None:
        """Initialize HyperDB provider.

        Args:
            persist_directory: Directory to persist the database. If None, uses ~/.pepperpy/hyperdb
            dimension: Dimension of vectors (default 1536 for text-embedding-3-small)
            metric: Distance metric to use (default: cosine)
            **kwargs: Additional configuration parameters
        """
        super().__init__()
        self.persist_directory = persist_directory or os.path.join(
            os.path.expanduser("~"),
            ".pepperpy/hyperdb",
        )
        self.dimension = dimension
        self.metric = metric
        self.kwargs = kwargs
        self._db: Optional[HyperDB] = None

    def _get_db(self) -> HyperDB:
        """Get the database, raising an error if not initialized.

        Returns:
            The initialized database

        Raises:
            ValidationError: If database is not initialized
        """
        if self._db is None:
            raise ValidationError("Database not initialized")
        return self._db

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates the database if it doesn't exist.
        """
        # Create database directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize database
        db = HyperDB(
            dim=self.dimension,
            metric=self.metric,
            path=self.persist_directory,
            **self.kwargs,
        )

        # Load existing data if any
        if os.path.exists(os.path.join(self.persist_directory, "db.hyper")):
            db.load()

        self._db = db

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._db is not None:
            self._db.save()  # Persist data before cleanup
            self._db = None

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in HyperDB.

        Args:
            docs: Document or list of documents to store
        """
        if isinstance(docs, Document):
            docs = [docs]

        for doc in docs:
            if "embeddings" not in doc.metadata:
                raise ValidationError("Document must have embeddings in metadata")

            doc_id = str(uuid.uuid4())
            self._get_db().add(
                vector=doc.metadata["embeddings"],
                id=doc_id,
                metadata={
                    "text": doc.text,
                    "metadata": doc.metadata,
                },
            )

        # Auto-save after each store operation
        self._get_db().save()

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

        results = self._get_db().search(
            query=query.embeddings,
            k=limit,
            **kwargs,
        )

        search_results = []
        for item_id, score in results:
            item = self._get_db().get(item_id)
            if item is None:
                continue

            search_results.append(
                SearchResult(
                    id=item_id,
                    text=item["metadata"]["text"],
                    metadata=item["metadata"]["metadata"],
                    score=1.0 - float(score),  # Convert distance to similarity
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
        item = self._get_db().get(doc_id)
        if item is None:
            return None

        return Document(
            text=item["metadata"]["text"],
            metadata=item["metadata"]["metadata"],
        )
