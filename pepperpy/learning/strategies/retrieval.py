"""Retrieval-based learning strategy implementation for Pepperpy."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from ...common.types import PepperpyObject, DictInitializable, Validatable
from ...common.errors import LearningError, RetrievalMatchError, ContextLengthError
from ...core.context import Context
from ...data.document import Document, DocumentStore
from ...models.embeddings import EmbeddingModel
from .base import LearningStrategy

logger = logging.getLogger(__name__)

class RetrievalLearning(LearningStrategy[str]):
    """Retrieval-based learning strategy implementation."""
    
    def __init__(
        self,
        name: str,
        document_store: DocumentStore,
        embedding_model: EmbeddingModel,
        max_context_length: int = 2000,
        min_similarity: float = 0.7,
        context: Optional[Context] = None,
    ) -> None:
        """Initialize retrieval-based learning strategy.
        
        Args:
            name: Strategy name
            document_store: Document store for retrieval
            embedding_model: Embedding model for similarity search
            max_context_length: Maximum context length (default: 2000)
            min_similarity: Minimum similarity threshold (default: 0.7)
            context: Optional execution context
        """
        super().__init__(name, context)
        self._document_store = document_store
        self._embedding_model = embedding_model
        self._max_context_length = max_context_length
        self._min_similarity = min_similarity
        
    async def add_document(self, document: Document) -> None:
        """Add document to store.
        
        Args:
            document: Document to add
            
        Raises:
            LearningError: If strategy is not initialized
        """
        if not self._initialized:
            raise LearningError("Learning strategy not initialized")
            
        await self._document_store.add([document])
        logger.debug(f"Added document to store: {document}")
        
    async def _execute(self, query: str) -> List[Document]:
        """Retrieve relevant documents for query.
        
        Args:
            query: Query text to find documents for
            
        Returns:
            List of relevant documents
            
        Raises:
            RetrievalMatchError: If no relevant documents found
            ContextLengthError: If context length exceeds maximum
        """
        # Get query embedding
        embedding = await self._embedding_model.embed(query)
        
        # Search for relevant documents
        documents = await self._document_store.search(
            query=query,
            limit=10,  # Get more documents than needed for filtering
        )
        
        if not documents:
            raise RetrievalMatchError(
                message="No relevant documents found",
                query=query,
                min_similarity=self._min_similarity,
                documents_checked=10,
            )
            
        # Calculate total context length
        total_length = sum(len(doc.content) for doc in documents)
        
        if total_length > self._max_context_length:
            raise ContextLengthError(
                message="Context length exceeds maximum",
                max_length=self._max_context_length,
                current_length=total_length,
            )
            
        logger.debug(f"Found {len(documents)} relevant documents for query: {query[:50]}...")
        
        return documents
        
    def validate(self) -> None:
        """Validate strategy state."""
        super().validate()
        
        if self._max_context_length <= 0:
            raise ValueError("Maximum context length must be positive")
            
        if not 0 <= self._min_similarity <= 1:
            raise ValueError("Minimum similarity must be between 0 and 1")
            
        self._document_store.validate()
        self._embedding_model.validate() 