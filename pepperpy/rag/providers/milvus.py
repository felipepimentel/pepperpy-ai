"""Milvus vector database provider for RAG."""

import uuid
from typing import Any, List, Optional, Sequence, Union

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from pepperpy.core.base import ValidationError
from pepperpy.rag.base import Document, Query, RAGProvider, SearchResult


class MilvusProvider(RAGProvider):
    """Milvus vector database provider for RAG."""

    def __init__(
        self,
        collection_name: str = "pepperpy",
        host: str = "localhost",
        port: int = 19530,
        user: str = "",
        password: str = "",
        dimension: int = 1536,  # Default for text-embedding-3-small
        **kwargs: Any,
    ) -> None:
        """Initialize Milvus provider.

        Args:
            collection_name: Name of the collection to use
            host: Milvus server host
            port: Milvus server port
            user: Username for authentication
            password: Password for authentication
            dimension: Dimension of vectors (default 1536 for text-embedding-3-small)
            **kwargs: Additional configuration parameters
        """
        super().__init__()
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dimension = dimension
        self.kwargs = kwargs
        self._collection: Optional[Collection] = None

    def _get_collection(self) -> Collection:
        """Get the collection, raising an error if not initialized.

        Returns:
            The initialized collection

        Raises:
            ValidationError: If collection is not initialized
        """
        if self._collection is None:
            raise ValidationError("Collection not initialized")
        return self._collection

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates the collection if it doesn't exist.
        """
        # Connect to Milvus
        connections.connect(
            alias="default",
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            **self.kwargs,
        )

        # Create collection if it doesn't exist
        if not utility.has_collection(self.collection_name):
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.VARCHAR,
                    is_primary=True,
                    max_length=36,
                ),
                FieldSchema(
                    name="text",
                    dtype=DataType.VARCHAR,
                    max_length=65535,
                ),
                FieldSchema(
                    name="metadata",
                    dtype=DataType.JSON,
                ),
                FieldSchema(
                    name="vector",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.dimension,
                ),
            ]
            schema = CollectionSchema(
                fields=fields,
                description="PepperPy RAG collection",
            )
            collection = Collection(
                name=self.collection_name,
                schema=schema,
            )
            # Create index for vector field
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024},
            }
            collection.create_index(
                field_name="vector",
                index_params=index_params,
            )
            self._collection = collection
        else:
            self._collection = Collection(self.collection_name)

        # Load collection into memory
        self._get_collection().load()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._collection is not None:
            self._collection.release()
        connections.disconnect("default")

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in Milvus.

        Args:
            docs: Document or list of documents to store
        """
        if isinstance(docs, Document):
            docs = [docs]

        ids = []
        texts = []
        metadatas = []
        vectors = []

        for doc in docs:
            if "embeddings" not in doc.metadata:
                raise ValidationError("Document must have embeddings in metadata")

            doc_id = str(uuid.uuid4())
            ids.append(doc_id)
            texts.append(doc.text)
            metadatas.append(doc.metadata)
            vectors.append(doc.metadata["embeddings"])

        self._get_collection().insert([
            ids,
            texts,
            metadatas,
            vectors,
        ])

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

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10},
            **kwargs,
        }

        results = self._get_collection().search(
            data=[query.embeddings],
            anns_field="vector",
            param=search_params,
            limit=limit,
            output_fields=["id", "text", "metadata"],
        )

        search_results = []
        for hits in results:
            for hit in hits:
                search_results.append(
                    SearchResult(
                        id=hit.entity.get("id"),
                        text=hit.entity.get("text"),
                        metadata=hit.entity.get("metadata"),
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
        results = self._get_collection().query(
            expr=f'id == "{doc_id}"',
            output_fields=["text", "metadata"],
        )

        if not results:
            return None

        result = results[0]
        return Document(
            text=result["text"],
            metadata=result["metadata"],
        )
