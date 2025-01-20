"""Base RAG workflow classes for Pepperpy."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar

from ...common.types import PepperpyObject, DictInitializable, Validatable
from ...common.errors import LearningError, RetrievalMatchError, ContextLengthError
from ...core.lifecycle import Lifecycle
from ...core.context import Context
from ...data.document import Document, DocumentStore
from ...models.embeddings import EmbeddingModel
from ...models.llm import LLMModel

T = TypeVar("T")

class RAGWorkflow(Lifecycle, ABC):
    """Base RAG workflow class."""
    
    def __init__(
        self,
        name: str,
        document_store: DocumentStore,
        embedding_model: EmbeddingModel,
        llm_model: LLMModel,
        max_context_length: int = 4000,
        min_similarity: float = 0.7,
        batch_size: int = 5,
        enable_metrics: bool = True,
        context: Optional[Context] = None,
    ) -> None:
        """Initialize RAG workflow.
        
        Args:
            name: Workflow name
            document_store: Document store
            embedding_model: Embedding model
            llm_model: Language model
            max_context_length: Maximum context length
            min_similarity: Minimum similarity threshold
            batch_size: Batch size for processing
            enable_metrics: Whether to enable metrics
            context: Optional execution context
        """
        super().__init__(name, context)
        self._document_store = document_store
        self._embedding_model = embedding_model
        self._llm_model = llm_model
        self._max_context_length = max_context_length
        self._min_similarity = min_similarity
        self._batch_size = batch_size
        self._enable_metrics = enable_metrics
        self._metrics: Dict[str, float] = {}
        self._initialized = False
        
    @property
    def is_initialized(self) -> bool:
        """Check if workflow is initialized."""
        return self._initialized
        
    async def _initialize(self) -> None:
        """Initialize workflow."""
        await self._document_store.initialize()
        await self._embedding_model.initialize()
        await self._llm_model.initialize()
        self._initialized = True
        
    async def _cleanup(self) -> None:
        """Clean up workflow."""
        await self._document_store.cleanup()
        await self._embedding_model.cleanup()
        await self._llm_model.cleanup()
        self._initialized = False
        
    @property
    def context(self) -> Optional[Context]:
        """Return execution context."""
        return self._context
        
    @property
    def metrics(self) -> Dict[str, float]:
        """Return workflow metrics."""
        return self._metrics
        
    async def add_document(self, document: Document) -> None:
        """Add document to store.
        
        Args:
            document: Document to add
            
        Raises:
            LearningError: If workflow is not initialized
        """
        if not self._initialized:
            raise LearningError("RAG workflow not initialized")
            
        await self._document_store.add([document])
        
    async def process(self, query: str) -> str:
        """Process query using RAG workflow.
        
        Args:
            query: Query text
            
        Returns:
            Generated response
            
        Raises:
            LearningError: If workflow is not initialized
            RetrievalMatchError: If no relevant documents found
            ContextLengthError: If context length exceeds maximum
        """
        if not self._initialized:
            raise LearningError("RAG workflow not initialized")
            
        # Get query embedding
        query_embedding = await self._embedding_model.embed(query)
        
        # Search for relevant documents
        documents = await self._document_store.search(
            query=query,
            limit=self._batch_size,
        )
        
        if not documents:
            raise RetrievalMatchError(
                message="No relevant documents found",
                query=query,
                min_similarity=self._min_similarity,
                documents_checked=self._batch_size,
            )
            
        # Calculate total context length
        total_length = sum(len(doc.content) for doc in documents)
        
        if total_length > self._max_context_length:
            raise ContextLengthError(
                message="Context length exceeds maximum",
                max_length=self._max_context_length,
                current_length=total_length,
            )
            
        # Generate response
        response = await self._generate_response(query, documents)
        
        # Update metrics
        if self._enable_metrics:
            self._metrics.update({
                "num_documents": len(documents),
                "context_length": total_length,
                "similarity_score": sum(doc.metadata.get("similarity", 0.0) for doc in documents) / len(documents),
            })
            
        return response
        
    @abstractmethod
    async def _generate_response(self, query: str, documents: List[Document]) -> str:
        """Generate response implementation."""
        pass
        
    def validate(self) -> None:
        """Validate workflow state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Workflow name cannot be empty")
            
        if self._max_context_length <= 0:
            raise ValueError("Maximum context length must be positive")
            
        if not 0 <= self._min_similarity <= 1:
            raise ValueError("Minimum similarity must be between 0 and 1")
            
        if self._batch_size <= 0:
            raise ValueError("Batch size must be positive")
            
        self._document_store.validate()
        self._embedding_model.validate()
        self._llm_model.validate()
        
        if self._context is not None:
            self._context.validate() 