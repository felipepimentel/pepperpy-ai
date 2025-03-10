"""Memory vector store provider implementation.

This module provides an in-memory vector store for storing and retrieving vectors.
"""

import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from numpy.linalg import norm

from pepperpy.errors import VectorStoreError
from pepperpy.rag.storage.base import BaseVectorStore
from pepperpy.rag.storage.types import (
    Collection,
    Document,
    DocumentChunk,
    DocumentMetadata,
    SearchResult,
)


class MemoryVectorStore(BaseVectorStore):
    """In-memory vector store implementation.

    This provider stores vectors and documents in memory using dictionaries and
    numpy arrays for efficient vector operations.
    """

    def __init__(self) -> None:
        """Initialize the memory vector store."""
        # Collection storage
        self._collections: Dict[str, Collection] = {}
        
        # Document storage
        self._docs: Dict[str, Dict[str, Document]] = {}
        
        # Vector storage
        self._vectors: Dict[str, Dict[str, np.ndarray]] = {}
        
        # Metadata storage
        self._metadata: Dict[str, Dict[str, DocumentMetadata]] = {}

    def _compute_similarity(
        self,
        query_vector: np.ndarray,
        doc_vectors: List[Tuple[str, np.ndarray]],
    ) -> List[Tuple[str, float]]:
        """Compute cosine similarity between query vector and document vectors.

        Args:
            query_vector: Query vector.
            doc_vectors: List of (doc_id, vector) tuples.

        Returns:
            List of (doc_id, score) tuples sorted by score in descending order.
        """
        # Normalize query vector
        query_norm = norm(query_vector)
        if query_norm == 0:
            return [(doc_id, 0.0) for doc_id, _ in doc_vectors]
        query_vector = query_vector / query_norm

        # Compute similarities
        similarities = []
        for doc_id, doc_vector in doc_vectors:
            # Normalize document vector
            doc_norm = norm(doc_vector)
            if doc_norm == 0:
                similarities.append((doc_id, 0.0))
                continue
            doc_vector = doc_vector / doc_norm

            # Compute cosine similarity
            similarity = float(np.dot(query_vector, doc_vector))
            similarities.append((doc_id, similarity))

        # Sort by similarity score
        return sorted(similarities, key=lambda x: x[1], reverse=True)

    async def add(
        self,
        collection_name: str,
        documents: Union[Document, List[Document]],
        **kwargs: Any,
    ) -> List[str]:
        """Add documents to a collection.

        Args:
            collection_name: Name of the collection.
            documents: Document or list of documents to add.
            **kwargs: Additional arguments.

        Returns:
            List of document IDs.

        Raises:
            VectorStoreError: If collection doesn't exist or documents are invalid.
        """
        try:
            # Ensure collection exists
            if collection_name not in self._collections:
                raise VectorStoreError(f"Collection {collection_name} does not exist")

            # Convert single document to list
            if isinstance(documents, Document):
                documents = [documents]

            # Initialize storage for collection if needed
            if collection_name not in self._docs:
                self._docs[collection_name] = {}
                self._vectors[collection_name] = {}
                self._metadata[collection_name] = {}

            # Add documents
            doc_ids = []
            for doc in documents:
                # Generate document ID
                doc_id = str(uuid.uuid4())
                doc_ids.append(doc_id)

                # Store document
                self._docs[collection_name][doc_id] = doc

                # Store vector
                if doc.vector is not None:
                    self._vectors[collection_name][doc_id] = np.array(doc.vector)

                # Store metadata
                if doc.metadata:
                    self._metadata[collection_name][doc_id] = doc.metadata

            return doc_ids

        except Exception as e:
            raise VectorStoreError(f"Error adding documents: {str(e)}") from e

    async def get(
        self,
        collection_name: str,
        doc_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> Union[Optional[Document], List[Optional[Document]]]:
        """Get documents by ID.

        Args:
            collection_name: Name of the collection.
            doc_ids: Document ID or list of document IDs.
            **kwargs: Additional arguments.

        Returns:
            Document or list of documents (None for non-existent IDs).

        Raises:
            VectorStoreError: If collection doesn't exist.
        """
        try:
            # Ensure collection exists
            if collection_name not in self._collections:
                raise VectorStoreError(f"Collection {collection_name} does not exist")

            # Convert single ID to list
            single_id = isinstance(doc_ids, str)
            if single_id:
                doc_ids = [doc_ids]

            # Get documents
            docs = []
            for doc_id in doc_ids:
                doc = self._docs.get(collection_name, {}).get(doc_id)
                if doc:
                    # Add vector and metadata if available
                    vector = self._vectors.get(collection_name, {}).get(doc_id)
                    metadata = self._metadata.get(collection_name, {}).get(doc_id)
                    doc = Document(
                        chunks=doc.chunks,
                        vector=vector.tolist() if vector is not None else None,
                        metadata=metadata,
                    )
                docs.append(doc)

            return docs[0] if single_id else docs

        except Exception as e:
            raise VectorStoreError(f"Error getting documents: {str(e)}") from e

    async def delete(
        self,
        collection_name: str,
        doc_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> List[str]:
        """Delete documents by ID.

        Args:
            collection_name: Name of the collection.
            doc_ids: Document ID or list of document IDs.
            **kwargs: Additional arguments.

        Returns:
            List of successfully deleted document IDs.

        Raises:
            VectorStoreError: If collection doesn't exist.
        """
        try:
            # Ensure collection exists
            if collection_name not in self._collections:
                raise VectorStoreError(f"Collection {collection_name} does not exist")

            # Convert single ID to list
            if isinstance(doc_ids, str):
                doc_ids = [doc_ids]

            # Delete documents
            deleted_ids = []
            for doc_id in doc_ids:
                # Remove from all storage
                doc_deleted = False
                if collection_name in self._docs:
                    doc_deleted = self._docs[collection_name].pop(doc_id, None) is not None
                if collection_name in self._vectors:
                    self._vectors[collection_name].pop(doc_id, None)
                if collection_name in self._metadata:
                    self._metadata[collection_name].pop(doc_id, None)

                if doc_deleted:
                    deleted_ids.append(doc_id)

            return deleted_ids

        except Exception as e:
            raise VectorStoreError(f"Error deleting documents: {str(e)}") from e

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        min_score: Optional[float] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search for similar documents.

        Args:
            collection_name: Name of the collection.
            query_vector: Query vector.
            limit: Maximum number of results.
            min_score: Minimum similarity score.
            filter: Metadata filter criteria.
            **kwargs: Additional arguments.

        Returns:
            List of search results sorted by similarity.

        Raises:
            VectorStoreError: If collection doesn't exist or search fails.
        """
        try:
            # Ensure collection exists
            if collection_name not in self._collections:
                raise VectorStoreError(f"Collection {collection_name} does not exist")

            # Convert query vector to numpy array
            query_vector_np = np.array(query_vector)

            # Get document vectors
            doc_vectors = []
            for doc_id, vector in self._vectors.get(collection_name, {}).items():
                # Apply metadata filter if provided
                if filter:
                    metadata = self._metadata.get(collection_name, {}).get(doc_id)
                    if not metadata:
                        continue
                    if not all(metadata.get(k) == v for k, v in filter.items()):
                        continue

                doc_vectors.append((doc_id, vector))

            # Compute similarities
            similarities = self._compute_similarity(query_vector_np, doc_vectors)

            # Filter by minimum score
            if min_score is not None:
                similarities = [
                    (doc_id, score)
                    for doc_id, score in similarities
                    if score >= min_score
                ]

            # Limit results
            similarities = similarities[:limit]

            # Create search results
            results = []
            for doc_id, score in similarities:
                doc = self._docs[collection_name][doc_id]
                vector = self._vectors[collection_name][doc_id]
                metadata = self._metadata.get(collection_name, {}).get(doc_id)

                result = SearchResult(
                    document=Document(
                        chunks=doc.chunks,
                        vector=vector.tolist(),
                        metadata=metadata,
                    ),
                    score=score,
                )
                results.append(result)

            return results

        except Exception as e:
            raise VectorStoreError(f"Error searching documents: {str(e)}") from e

    async def list_collections(self, **kwargs: Any) -> List[Collection]:
        """List all collections.

        Args:
            **kwargs: Additional arguments.

        Returns:
            List of collections.
        """
        return list(self._collections.values())

    async def get_collection(
        self,
        collection_name: str,
        **kwargs: Any,
    ) -> Optional[Collection]:
        """Get a collection by name.

        Args:
            collection_name: Name of the collection.
            **kwargs: Additional arguments.

        Returns:
            Collection if it exists, None otherwise.
        """
        return self._collections.get(collection_name)

    async def create_collection(
        self,
        collection_name: str,
        **kwargs: Any,
    ) -> Collection:
        """Create a new collection.

        Args:
            collection_name: Name of the collection.
            **kwargs: Additional arguments.

        Returns:
            Created collection.

        Raises:
            VectorStoreError: If collection already exists.
        """
        try:
            # Check if collection already exists
            if collection_name in self._collections:
                raise VectorStoreError(f"Collection {collection_name} already exists")

            # Create collection
            collection = Collection(name=collection_name)
            self._collections[collection_name] = collection

            return collection

        except Exception as e:
            raise VectorStoreError(f"Error creating collection: {str(e)}") from e

    async def delete_collection(
        self,
        collection_name: str,
        **kwargs: Any,
    ) -> bool:
        """Delete a collection.

        Args:
            collection_name: Name of the collection.
            **kwargs: Additional arguments.

        Returns:
            True if collection was deleted, False if it didn't exist.
        """
        try:
            # Remove from all storage
            deleted = False
            if collection_name in self._collections:
                del self._collections[collection_name]
                deleted = True
            if collection_name in self._docs:
                del self._docs[collection_name]
            if collection_name in self._vectors:
                del self._vectors[collection_name]
            if collection_name in self._metadata:
                del self._metadata[collection_name]

            return deleted

        except Exception as e:
            raise VectorStoreError(f"Error deleting collection: {str(e)}") from e

    async def clear(self, **kwargs: Any) -> None:
        """Clear all collections and data.

        Args:
            **kwargs: Additional arguments.
        """
        self._collections.clear()
        self._docs.clear()
        self._vectors.clear()
        self._metadata.clear()
