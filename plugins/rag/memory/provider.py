"""Simple in-memory RAG provider for testing and examples."""

import uuid
from collections.abc import Sequence
from typing import Any, Dict, List, Optional, Union

from pepperpy.rag.base import Document, Query, RAGProvider, SearchResult


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Cosine similarity (0.0 to 1.0)
    """
    if not a or not b:
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class DocumentEntry:
    """Document entry for in-memory storage."""

    def __init__(
        self,
        id: str,
        text: str,
        metadata: Dict[str, Any],
        vector: Optional[List[float]] = None,
    ) -> None:
        """Initialize document entry.

        Args:
            id: Document ID
            text: Document text
            metadata: Document metadata
            vector: Optional embedding vector
        """
        self.id = id
        self.text = text
        self.metadata = metadata
        self.vector = vector


class InMemoryProvider(RAGProvider):
    """Simple in-memory RAG provider for testing and examples."""

    name = "memory"

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str

    def __init__(
        self,
        collection_name: str = "default",
        **kwargs: Any,
    ) -> None:
        """Initialize in-memory provider.

        Args:
            collection_name: Name for the collection (for compatibility)
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.collection_name = collection_name
        self._documents: Dict[str, DocumentEntry] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider.

        For the in-memory provider, this just marks it as initialized.
        """
        self._initialized = True

    async def store_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Store a document in memory.

        Args:
            text: Document text
            metadata: Optional document metadata
            document_id: Optional document ID (generated if not provided)
            **kwargs: Additional options

        Returns:
            The document ID
        """
        if not self._initialized:
            await self.initialize()

        # Generate ID if not provided
        doc_id = document_id or str(uuid.uuid4())

        # Create document entry
        self._documents[doc_id] = DocumentEntry(
            id=doc_id,
            text=text,
            metadata=metadata or {},
            vector=None,  # Vector will be set when embeddings are generated
        )

        return doc_id

    async def retrieve_document(
        self,
        document_id: str,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID.

        Args:
            document_id: Document ID
            **kwargs: Additional options

        Returns:
            Document data or None if not found
        """
        if not self._initialized:
            await self.initialize()

        doc = self._documents.get(document_id)
        if not doc:
            return None

        return {
            "id": doc.id,
            "text": doc.text,
            "metadata": doc.metadata,
            "vector": doc.vector,
        }

    async def delete_document(
        self,
        document_id: str,
        **kwargs: Any,
    ) -> None:
        """Delete a document by ID.

        Args:
            document_id: Document ID
            **kwargs: Additional options
        """
        if not self._initialized:
            await self.initialize()

        if document_id in self._documents:
            del self._documents[document_id]

    async def update_document(
        self,
        document_id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Update a document's text or metadata.

        Args:
            document_id: Document ID
            text: New text (if None, text is not updated)
            metadata: New metadata (if None, metadata is not updated)
            **kwargs: Additional options
        """
        if not self._initialized:
            await self.initialize()

        doc = self._documents.get(document_id)
        if not doc:
            return

        if text is not None:
            doc.text = text
            # Text changed, clear vector to force regeneration
            doc.vector = None

        if metadata is not None:
            doc.metadata = metadata

    async def search_documents(
        self,
        query: str,
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Search for documents.

        Args:
            query: Search query text
            limit: Maximum number of results to return
            filter_metadata: Optional metadata filter
            **kwargs: Additional options

        Returns:
            List of matching documents
        """
        if not self._initialized:
            await self.initialize()

        # Get embeddings for the query
        query_embedding = kwargs.get("query_embedding")

        results = []

        # If we have query embeddings and document embeddings, use vector search
        if query_embedding:
            results = await self._vector_search(
                query_embedding=query_embedding,
                limit=limit,
                filter_metadata=filter_metadata,
            )
        else:
            # Fall back to simple text search
            results = await self._text_search(
                query=query, limit=limit, filter_metadata=filter_metadata
            )

        return results

    async def _vector_search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search using vector similarity.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of matching documents with scores
        """
        # Filter documents that have vectors and match metadata filter
        docs = self._documents.values()

        if filter_metadata:
            docs = [
                d
                for d in docs
                if d.vector and self._matches_filter(d.metadata, filter_metadata)
            ]
        else:
            docs = [d for d in docs if d.vector]

        # Calculate similarities
        similarities = []
        for doc in docs:
            if doc.vector:
                score = cosine_similarity(query_embedding, doc.vector)
                similarities.append((score, doc))

        # Sort by similarity (highest first)
        similarities.sort(reverse=True, key=lambda x: x[0])

        # Convert to result format
        results = []
        for score, doc in similarities[:limit]:
            results.append(
                {
                    "id": doc.id,
                    "text": doc.text,
                    "metadata": doc.metadata,
                    "score": float(score),
                }
            )

        return results

    async def _text_search(
        self,
        query: str,
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search using simple text matching.

        Args:
            query: Search query text
            limit: Maximum number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of matching documents with scores
        """
        # Simple text search (case insensitive)
        query_lower = query.lower()
        matches = []

        for doc in self._documents.values():
            # Skip if doesn't match metadata filter
            if filter_metadata and not self._matches_filter(
                doc.metadata, filter_metadata
            ):
                continue

            # Simple text matching score (very basic)
            text_lower = doc.text.lower()
            if query_lower in text_lower:
                # Calculate a simple score based on frequency and position
                score = text_lower.count(query_lower) / (
                    text_lower.find(query_lower) + 1
                )
                matches.append((score, doc))
            else:
                # Check for partial word matches
                words = query_lower.split()
                matched_words = sum(1 for word in words if word in text_lower)
                if matched_words > 0:
                    score = 0.1 * (matched_words / len(words))
                    matches.append((score, doc))

        # Sort by score
        matches.sort(reverse=True, key=lambda x: x[0])

        # Convert to result format
        results = []
        for score, doc in matches[:limit]:
            results.append(
                {
                    "id": doc.id,
                    "text": doc.text,
                    "metadata": doc.metadata,
                    "score": float(score),
                }
            )

        return results

    def _matches_filter(
        self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]
    ) -> bool:
        """Check if metadata matches filter.

        Args:
            metadata: Document metadata
            filter_metadata: Filter criteria

        Returns:
            True if metadata matches filter
        """
        for key, value in filter_metadata.items():
            if key not in metadata:
                return False

            if isinstance(value, dict):
                # Nested filter
                if not isinstance(metadata[key], dict):
                    return False
                if not self._matches_filter(metadata[key], value):
                    return False
            elif metadata[key] != value:
                return False

        return True

    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Add multiple texts at once.

        Args:
            texts: List of texts to add
            metadatas: Optional list of metadata for each text
            **kwargs: Additional options

        Returns:
            List of document IDs
        """
        if not self._initialized:
            await self.initialize()

        # Use empty dict if metadatas is None
        if metadatas is None:
            metadatas = [{} for _ in texts]

        # Ensure metadatas list matches texts list
        if len(metadatas) < len(texts):
            metadatas.extend({} for _ in range(len(texts) - len(metadatas)))

        # Add each document
        doc_ids = []
        for i, text in enumerate(texts):
            doc_id = await self.store_document(
                text=text, metadata=metadatas[i], **kwargs
            )
            doc_ids.append(doc_id)

        return doc_ids

    async def add_embeddings(
        self,
        document_ids: List[str],
        embeddings: List[List[float]],
        **kwargs: Any,
    ) -> None:
        """Add embeddings for documents.

        Args:
            document_ids: List of document IDs
            embeddings: List of embedding vectors
            **kwargs: Additional options
        """
        if not self._initialized:
            await self.initialize()

        # Ensure lists match in length
        if len(document_ids) != len(embeddings):
            raise ValueError("document_ids and embeddings must have the same length")

        # Add embeddings to documents
        for i, doc_id in enumerate(document_ids):
            if doc_id in self._documents:
                self._documents[doc_id].vector = embeddings[i]

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """List all documents.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            **kwargs: Additional options

        Returns:
            List of documents
        """
        if not self._initialized:
            await self.initialize()

        # Get all documents, sorted by ID for consistency
        all_docs = sorted(self._documents.values(), key=lambda d: d.id)

        # Apply offset and limit
        paged_docs = all_docs[offset : offset + limit]

        # Convert to result format
        results = []
        for doc in paged_docs:
            results.append(
                {
                    "id": doc.id,
                    "text": doc.text,
                    "metadata": doc.metadata,
                    "vector": doc.vector,
                }
            )

        return results

    async def clear(self, **kwargs: Any) -> None:
        """Clear all documents.

        Args:
            **kwargs: Additional options
        """
        if not self._initialized:
            await self.initialize()

        self._documents.clear()

    async def count_documents(self, **kwargs: Any) -> int:
        """Get total number of documents.

        Args:
            **kwargs: Additional options

        Returns:
            Number of documents
        """
        if not self._initialized:
            await self.initialize()

        return len(self._documents)

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.

        Returns:
            Dictionary containing statistics
        """
        return {
            "count": await self.count_documents(),
            "name": self.collection_name,
            "type": "in-memory",
            "has_vectors": sum(
                1 for doc in self._documents.values() if doc.vector is not None
            ),
        }

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in the RAG context.

        Args:
            docs: Document or list of documents to store.
        """
        if not self._initialized:
            await self.initialize()

        if isinstance(docs, list):
            for doc in docs:
                await self.store_document(doc.text, doc.metadata)
        else:
            await self.store_document(docs.text, docs.metadata)

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
        if not self._initialized:
            await self.initialize()

        # Convert query to Query object if needed
        if isinstance(query, str):
            query = Query(text=query)

        # Get query vector
        query_vector = query.embeddings

        # Collect results
        results = []
        for doc_id, doc in self._documents.items():
            # Calculate similarity if vectors available
            score = 0.0
            if query_vector and doc.vector:
                score = cosine_similarity(query_vector, doc.vector)

            # Add to results
            results.append(
                SearchResult(
                    id=doc_id,
                    text=doc.text,
                    metadata=doc.metadata,
                    score=score,
                )
            )

        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def get(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID.

        Args:
            doc_id: ID of the document to get

        Returns:
            The document if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        doc = self._documents.get(doc_id)
        if not doc:
            return None

        return Document(
            text=doc.text,
            metadata=doc.metadata,
        )
