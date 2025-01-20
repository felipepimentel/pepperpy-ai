"""RAG learning strategy implementation."""

import logging
from typing import Any, Dict, List, Optional

from ..common.errors import PepperpyError
from ..models.llm import LLMModel
from ..models.types import Message
from .base import LearningStrategy, LearningError


logger = logging.getLogger(__name__)


class RAGStrategy(LearningStrategy):
    """RAG (Retrieval-Augmented Generation) learning strategy implementation."""
    
    def __init__(
        self,
        name: str,
        model: LLMModel,
        retriever: Any,  # TODO: Add proper type
        max_chunks: int = 5,
        min_score: float = 0.5,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize RAG strategy.
        
        Args:
            name: Strategy name
            model: Language model
            retriever: Document retriever
            max_chunks: Maximum number of chunks to retrieve
            min_score: Minimum relevance score for chunks
            config: Optional strategy configuration
        """
        super().__init__(name, config)
        self._model = model
        self._retriever = retriever
        self._max_chunks = max_chunks
        self._min_score = min_score
        
    @property
    def model(self) -> LLMModel:
        """Return language model."""
        return self._model
        
    @property
    def retriever(self) -> Any:
        """Return document retriever."""
        return self._retriever
        
    @property
    def max_chunks(self) -> int:
        """Return maximum number of chunks."""
        return self._max_chunks
        
    @property
    def min_score(self) -> float:
        """Return minimum relevance score."""
        return self._min_score
        
    async def _initialize(self) -> None:
        """Initialize RAG strategy."""
        await super()._initialize()
        await self._model.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up RAG strategy."""
        await super()._cleanup()
        await self._model.cleanup()
        
    async def train(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Train on input data.
        
        Args:
            input_data: Input data
            context: Optional training context
            
        Returns:
            Training result
            
        Raises:
            LearningError: If training fails
        """
        try:
            # Add documents to retriever
            if isinstance(input_data, (str, bytes)):
                documents = [input_data]
            elif isinstance(input_data, (list, tuple)):
                documents = input_data
            else:
                raise LearningError(f"Invalid input type: {type(input_data)}")
                
            # Process and index documents
            for doc in documents:
                await self._retriever.add(doc)
                
            return {"status": "success", "documents": len(documents)}
            
        except Exception as e:
            raise LearningError(f"RAG training failed: {e}") from e
            
    async def evaluate(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Evaluate on input data.
        
        Args:
            input_data: Input data
            context: Optional evaluation context
            
        Returns:
            Evaluation result
            
        Raises:
            LearningError: If evaluation fails
        """
        try:
            # Convert input to query
            if isinstance(input_data, str):
                query = input_data
            else:
                raise LearningError(f"Invalid input type: {type(input_data)}")
                
            # Retrieve relevant chunks
            results = await self._retriever.search(
                query,
                limit=self._max_chunks,
                min_score=self._min_score,
            )
            
            # Build prompt with retrieved context
            prompt = "Context:\n"
            for result in results:
                prompt += f"- {result.content}\n"
                
            prompt += f"\nQuery: {query}\n"
            prompt += "Answer:"
            
            # Generate response
            message = Message(role="user", content=prompt)
            response = await self._model.generate([message])
            
            return {
                "query": query,
                "chunks": len(results),
                "response": response.content,
            }
            
        except Exception as e:
            raise LearningError(f"RAG evaluation failed: {e}") from e
            
    def validate(self) -> None:
        """Validate RAG strategy state."""
        super().validate()
        
        if not self._model:
            raise ValueError("Language model not provided")
            
        if not self._retriever:
            raise ValueError("Document retriever not provided")
            
        if self._max_chunks < 1:
            raise ValueError("Maximum chunks must be greater than 0")
            
        if not 0 <= self._min_score <= 1:
            raise ValueError("Minimum score must be between 0 and 1") 