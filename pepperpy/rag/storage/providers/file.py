"""File vector store provider implementation.

This module provides functionality for storing and retrieving vectors in files.
"""

import json
import pickle
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from numpy.linalg import norm

from pepperpy.errors import VectorStoreError
from pepperpy.rag.storage.base import BaseVectorStore
from pepperpy.rag.storage.types import Collection, Document, SearchResult


class FileVectorStore(BaseVectorStore):
    """File-based vector store implementation.

    This provider stores vectors and documents in files using either JSON or
    pickle format for persistence.
    """

    def __init__(
        self,
        directory: Union[str, Path] = "./vector_store",
        format: str = "json",
        **kwargs: Any,
    ) -> None:
        """Initialize the file vector store.

        Args:
            directory: Directory to store files in.
            format: Storage format ('json' or 'pickle').
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.directory = Path(directory)
        self.format = format

        # Validate format
        if format not in ["json", "pickle"]:
            raise ValueError(f"Unsupported format: {format}")

        # Create directory if it doesn't exist
        self.directory.mkdir(parents=True, exist_ok=True)

        # Initialize storage
        self._collections: Dict[str, Collection] = {}
        self._docs: Dict[str, Dict[str, Document]] = {}
        self._vectors: Dict[str, Dict[str, np.ndarray]] = {}
        self._metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Load existing data
        self._load()

    def _get_collection_path(self, collection_name: str) -> Path:
        """Get the file path for a collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            Path to the collection file.
        """
        extension = ".json" if self.format == "json" else ".pkl"
        return self.directory / f"{collection_name}{extension}"

    def _save_collection(self, collection_name: str) -> None:
        """Save a collection to file.

        Args:
            collection_name: Name of the collection to save.

        Raises:
            VectorStoreError: If saving fails.
        """
        try:
            # Prepare data for saving
            data = {
                "collection": self._collections[collection_name].dict(),
                "documents": {
                    k: doc.dict()
                    for k, doc in self._docs.get(collection_name, {}).items()
                },
                "vectors": {
                    k: v.tolist()
                    for k, v in self._vectors.get(collection_name, {}).items()
                },
                "metadata": self._metadata.get(collection_name, {}),
            }

            # Save to file
            path = self._get_collection_path(collection_name)
            if self.format == "json":
                with open(path, "w") as f:
                    json.dump(data, f)
            else:
                with open(path, "wb") as f:
                    pickle.dump(data, f)

        except Exception as e:
            raise VectorStoreError(f"Error saving collection: {str(e)}") from e

    def _load_collection(self, collection_name: str) -> None:
        """Load a collection from file.

        Args:
            collection_name: Name of the collection to load.

        Raises:
            VectorStoreError: If loading fails.
        """
        try:
            path = self._get_collection_path(collection_name)
            if not path.exists():
                return

            # Load from file
            if self.format == "json":
                with open(path, "r") as f:
                    data = json.load(f)
            else:
                with open(path, "rb") as f:
                    data = pickle.load(f)

            # Restore data
            self._collections[collection_name] = Collection(**data["collection"])
            self._docs[collection_name] = {
                k: Document(**doc) for k, doc in data["documents"].items()
            }
            self._vectors[collection_name] = {
                k: np.array(v) for k, v in data["vectors"].items()
            }
            self._metadata[collection_name] = data["metadata"]

        except Exception as e:
            raise VectorStoreError(f"Error loading collection: {str(e)}") from e

    def _load(self) -> None:
        """Load all collections from files.

        Raises:
            VectorStoreError: If loading fails.
        """
        try:
            # Get all collection files
            pattern = "*.json" if self.format == "json" else "*.pkl"
            for path in self.directory.glob(pattern):
                collection_name = path.stem
                self._load_collection(collection_name)

        except Exception as e:
            raise VectorStoreError(f"Error loading collections: {str(e)}") from e

    def _compute_similarity(
        self,
        query_vector: np.ndarray,
        doc_vectors: List[tuple[str, np.ndarray]],
    ) -> List[tuple[str, float]]:
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

            # Save collection
            self._save_collection(collection_name)

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
                    doc_deleted = (
                        self._docs[collection_name].pop(doc_id, None) is not None
                    )
                if collection_name in self._vectors:
                    self._vectors[collection_name].pop(doc_id, None)
                if collection_name in self._metadata:
                    self._metadata[collection_name].pop(doc_id, None)

                if doc_deleted:
                    deleted_ids.append(doc_id)

            # Save collection
            if deleted_ids:
                self._save_collection(collection_name)

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

            # Save collection
            self._save_collection(collection_name)

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
            # Remove from memory
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

            # Remove file
            if deleted:
                path = self._get_collection_path(collection_name)
                if path.exists():
                    path.unlink()

            return deleted

        except Exception as e:
            raise VectorStoreError(f"Error deleting collection: {str(e)}") from e

    async def clear(self, **kwargs: Any) -> None:
        """Clear all collections and data.

        Args:
            **kwargs: Additional arguments.
        """
        try:
            # Clear memory
            self._collections.clear()
            self._docs.clear()
            self._vectors.clear()
            self._metadata.clear()

            # Remove all files
            pattern = "*.json" if self.format == "json" else "*.pkl"
            for path in self.directory.glob(pattern):
                path.unlink()

        except Exception as e:
            raise VectorStoreError(f"Error clearing vector store: {str(e)}") from e
