"""Semantic search strategy for RAG capabilities."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast

import numpy as np
from sentence_transformers import SentenceTransformer

from ..base import Document
from .base import BaseRAGStrategy, RAGStrategyConfig


@dataclass
class SemanticRAGConfig(RAGStrategyConfig):
    """Configuration for semantic RAG strategy.
    
    Attributes:
        model_name: The name of the sentence transformer model to use.
        device: The device to use for model inference (e.g., "cpu", "cuda").
        normalize_embeddings: Whether to normalize embeddings to unit length.
        batch_size: The batch size for computing embeddings.
    """

    model_name: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    normalize_embeddings: bool = True
    batch_size: int = 32
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticRAGStrategy(BaseRAGStrategy):
    """Semantic search strategy for RAG capabilities.
    
    This strategy uses sentence transformers to compute document embeddings
    and performs semantic search using cosine similarity.
    """

    def __init__(self, config: SemanticRAGConfig) -> None:
        """Initialize the semantic RAG strategy.

        Args:
            config: The strategy configuration.
        """
        super().__init__(config)
        self.config = cast(SemanticRAGConfig, config)
        self._model: Optional[SentenceTransformer] = None
        self._embeddings: Optional[np.ndarray] = None

    async def initialize(self) -> None:
        """Initialize the strategy.
        
        This method loads the sentence transformer model and initializes
        the embeddings array.
        """
        self._model = SentenceTransformer(
            self.config.model_name,
            device=self.config.device,
        )
        if self._model is not None:
            self._embeddings = np.zeros((0, self._model.get_sentence_embedding_dimension()))

    async def cleanup(self) -> None:
        """Clean up resources used by the strategy."""
        self._model = None
        self._embeddings = None
        self._documents.clear()

    async def process_document(self, document: Document) -> Document:
        """Process a document for storage.

        This method computes the document embedding if not already present.

        Args:
            document: The document to process.

        Returns:
            The processed document with embedding.
        """
        if document.embedding is None and self._model is not None:
            embedding = self._model.encode(
                document.content,
                normalize_embeddings=self.config.normalize_embeddings,
                batch_size=self.config.batch_size,
            )
            document.embedding = embedding.tolist()
        return document

    async def add_document(self, document: Document) -> None:
        """Add a document to the strategy.

        Args:
            document: The document to add.
        """
        if len(self._documents) >= self.config.max_documents:
            raise ValueError(
                f"Maximum number of documents ({self.config.max_documents}) reached"
            )
        processed_doc = await self.process_document(document)
        if processed_doc.embedding is not None and self._embeddings is not None:
            self._embeddings = np.vstack(
                [self._embeddings, np.array(processed_doc.embedding)]
            )
        self._documents.append(processed_doc)

    async def remove_document(self, document: Document) -> None:
        """Remove a document from the strategy.

        Args:
            document: The document to remove.
        """
        try:
            idx = self._documents.index(document)
            self._documents.remove(document)
            if self._embeddings is not None:
                self._embeddings = np.delete(self._embeddings, idx, axis=0)
        except ValueError:
            pass

    async def search(self, query: str, top_k: int = 5) -> List[Document]:
        """Search for documents similar to the query.

        This method computes the query embedding and returns the most similar
        documents based on cosine similarity.

        Args:
            query: The search query.
            top_k: The maximum number of documents to return.

        Returns:
            A list of documents sorted by relevance.
        """
        if not self._documents or self._model is None or self._embeddings is None:
            return []

        # Compute query embedding
        query_embedding = self._model.encode(
            query,
            normalize_embeddings=self.config.normalize_embeddings,
            batch_size=self.config.batch_size,
        )

        # Compute cosine similarities
        similarities = np.dot(self._embeddings, query_embedding)
        if self.config.normalize_embeddings:
            similarities = (similarities + 1) / 2  # Scale to [0, 1]

        # Get top-k documents
        top_k = min(top_k, len(self._documents))
        top_indices = np.argpartition(similarities, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(similarities[top_indices])][::-1]

        # Filter by similarity threshold
        results = []
        for idx in top_indices:
            if similarities[idx] >= self.config.similarity_threshold:
                results.append(self._documents[idx])
        return results

    async def clear(self) -> None:
        """Clear all documents from the strategy."""
        self._documents.clear()
        if self._embeddings is not None:
            self._embeddings = np.zeros((0, self._embeddings.shape[1])) 