"""Learning strategies module for Pepperpy.

This module provides various learning strategies including:
- RAG (Retrieval Augmented Generation)
- Fine-tuning
- In-context learning
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.types import PepperpyObject, DictInitializable, Validatable
from pepperpy.core.utils.errors import LearningError, RetrievalMatchError, ContextLengthError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.context import Context
from pepperpy.persistence.storage.document import Document, DocumentStore
from pepperpy.providers.embeddings.base import BaseEmbeddingProvider
from pepperpy.providers.llm.base import BaseLLMProvider

from .rag.rag import RAGStrategy
from .rag.basic import BasicRAGWorkflow
from .rag.pipeline import RAGPipeline
from .fine_tuning.strategy import FineTuningStrategy

T = TypeVar("T")


class LearningStrategy(Lifecycle, ABC):
    """Base class for learning strategies."""
    
    def __init__(
        self,
        name: str,
        document_store: DocumentStore,
        embedding_model: BaseEmbeddingProvider,
        llm_model: BaseLLMProvider,
        max_context_length: int = 4000,
        min_similarity: float = 0.7,
        batch_size: int = 5,
        enable_metrics: bool = True,
        context: Optional[Context] = None,
    ) -> None:
        """Initialize learning strategy.
        
        Args:
            name: Strategy name
            document_store: Document store
            embedding_model: Embedding model
            llm_model: Language model
            max_context_length: Maximum context length
            min_similarity: Minimum similarity threshold
            batch_size: Batch size for processing
            enable_metrics: Whether to enable metrics
            context: Optional execution context
        """
        super().__init__(name)
        self._document_store = document_store
        self._embedding_model = embedding_model
        self._llm_model = llm_model
        self._max_context_length = max_context_length
        self._min_similarity = min_similarity
        self._batch_size = batch_size
        self._enable_metrics = enable_metrics
        self._context = context
        self._metrics: Dict[str, float] = {}
        self._initialized = False
        
    @property
    def is_initialized(self) -> bool:
        """Check if strategy is initialized."""
        return self._initialized
        
    async def _initialize(self) -> None:
        """Initialize strategy."""
        self._document_store.initialize()
        await self._embedding_model.initialize()
        await self._llm_model.initialize()
        self._initialized = True
        
    async def _cleanup(self) -> None:
        """Clean up strategy."""
        self._document_store.cleanup()
        await self._embedding_model.cleanup()
        await self._llm_model.cleanup()
        self._initialized = False
        
    @property
    def context(self) -> Optional[Context]:
        """Return context."""
        return self._context
        
    @property
    def metrics(self) -> Dict[str, float]:
        """Return metrics."""
        return self._metrics.copy()
        
    async def add_document(self, document: Document) -> None:
        """Add document to store.
        
        Args:
            document: Document to add
        """
        if not self.is_initialized:
            raise LearningError("Strategy not initialized")
            
        self._document_store.add_document(document)
        
    async def process(self, query: str) -> str:
        """Process query using learning strategy.
        
        Args:
            query: Query to process
            
        Returns:
            Generated response
            
        Raises:
            LearningError: If strategy not initialized
            RetrievalMatchError: If no relevant documents found
            ContextLengthError: If context length exceeded
        """
        if not self.is_initialized:
            raise LearningError("Strategy not initialized")
            
        # Search for relevant documents
        documents = self._document_store.filter_by_metadata({
            "query": query,
            "min_similarity": self._min_similarity,
            "max_documents": self._batch_size,
        })
        
        if not documents:
            raise RetrievalMatchError("No relevant documents found")
            
        # Check context length
        total_length = sum(len(doc.content) for doc in documents)
        if total_length > self._max_context_length:
            raise ContextLengthError(
                "Context length exceeded",
                details={
                    "max_length": self._max_context_length,
                    "current_length": total_length,
                }
            )
            
        # Generate response
        response = await self._generate_response(query, documents)
        
        return response
        
    @abstractmethod
    async def _generate_response(self, query: str, documents: List[Document]) -> str:
        """Generate response from query and documents.
        
        Args:
            query: Query to process
            documents: Relevant documents
            
        Returns:
            Generated response
        """
        pass
        
    def validate(self) -> None:
        """Validate strategy configuration."""
        if not self._document_store:
            raise ValueError("Document store not set")
        if not self._embedding_model:
            raise ValueError("Embedding model not set")
        if not self._llm_model:
            raise ValueError("Language model not set")
            
        self._document_store.validate()
        self._embedding_model.validate()
        self._llm_model.validate()
        
        if self._context:
            self._context.validate()


__all__ = [
    "LearningStrategy",
    "RAGStrategy",
    "BasicRAGWorkflow",
    "RAGPipeline",
    "FineTuningStrategy",
]
