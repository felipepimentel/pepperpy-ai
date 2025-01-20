"""In-context learning strategy implementation for Pepperpy."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from ...common.types import PepperpyObject, DictInitializable, Validatable
from ...common.errors import LearningError, ExampleMatchError, ExampleLimitError
from ...core.context import Context
from ...data.vector import VectorStore
from ...models.embeddings import EmbeddingModel
from .base import LearningStrategy

logger = logging.getLogger(__name__)

class Example(PepperpyObject, DictInitializable, Validatable):
    """Example class for in-context learning."""
    
    def __init__(
        self,
        input_text: str,
        output_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize example.
        
        Args:
            input_text: Input text
            output_text: Output text
            metadata: Optional example metadata
        """
        self._input_text = input_text
        self._output_text = output_text
        self._metadata = metadata or {}
        
    @property
    def input_text(self) -> str:
        """Return input text."""
        return self._input_text
        
    @property
    def output_text(self) -> str:
        """Return output text."""
        return self._output_text
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return example metadata."""
        return self._metadata
        
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"{self.__class__.__name__}("
            f"input_text={self.input_text[:50]}..., "
            f"output_text={self.output_text[:50]}..."
            f")"
        )
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Example":
        """Create example from dictionary."""
        return cls(
            input_text=data["input_text"],
            output_text=data["output_text"],
            metadata=data.get("metadata"),
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert example to dictionary."""
        return {
            "input_text": self.input_text,
            "output_text": self.output_text,
            "metadata": self.metadata,
        }
        
    def validate(self) -> None:
        """Validate example state."""
        if not self.input_text:
            raise ValueError("Input text cannot be empty")
            
        if not self.output_text:
            raise ValueError("Output text cannot be empty")

class InContextLearning(LearningStrategy[str]):
    """In-context learning strategy implementation."""
    
    def __init__(
        self,
        name: str,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        max_examples: int = 5,
        similarity_threshold: float = 0.8,
        context: Optional[Context] = None,
    ) -> None:
        """Initialize in-context learning strategy.
        
        Args:
            name: Strategy name
            vector_store: Vector store for examples
            embedding_model: Embedding model for similarity search
            max_examples: Maximum number of examples (default: 5)
            similarity_threshold: Minimum similarity threshold (default: 0.8)
            context: Optional execution context
        """
        super().__init__(name, context)
        self._vector_store = vector_store
        self._embedding_model = embedding_model
        self._max_examples = max_examples
        self._similarity_threshold = similarity_threshold
        
    async def add_example(self, example: Example) -> None:
        """Add example to vector store.
        
        Args:
            example: Example to add
            
        Raises:
            LearningError: If strategy is not initialized
            ExampleLimitError: If maximum number of examples is reached
        """
        if not self._initialized:
            raise LearningError("Learning strategy not initialized")
            
        # Get current example count
        count = len(await self._vector_store.search(
            query=await self._embedding_model.embed(""),
            k=self._max_examples + 1,
        ))
        
        if count >= self._max_examples:
            raise ExampleLimitError(
                message="Maximum number of examples reached",
                max_examples=self._max_examples,
                current_examples=count,
            )
            
        # Add example to vector store
        embedding = await self._embedding_model.embed(example.input_text)
        await self._vector_store.add(embedding)
        
        logger.debug(f"Added example to vector store: {example}")
        
    async def _execute(self, input_text: str) -> List[Example]:
        """Find similar examples for input text.
        
        Args:
            input_text: Input text to find examples for
            
        Returns:
            List of similar examples
            
        Raises:
            ExampleMatchError: If no similar examples found
        """
        # Get input embedding
        embedding = await self._embedding_model.embed(input_text)
        
        # Search for similar examples
        results = await self._vector_store.search(
            query=embedding,
            k=self._max_examples,
            min_similarity=self._similarity_threshold,
        )
        
        if not results:
            raise ExampleMatchError(
                message="No similar examples found",
                query=input_text,
                similarity_threshold=self._similarity_threshold,
                examples_checked=self._max_examples,
            )
            
        # Convert results to examples
        examples = []
        for id_, similarity in results:
            example_data = await self._vector_store.get(id_)
            if example_data:
                example = Example.from_dict(example_data)
                examples.append(example)
            
        logger.debug(f"Found {len(examples)} similar examples for input: {input_text[:50]}...")
        
        return examples
        
    def validate(self) -> None:
        """Validate strategy state."""
        super().validate()
        
        if self._max_examples <= 0:
            raise ValueError("Maximum number of examples must be positive")
            
        if not 0 <= self._similarity_threshold <= 1:
            raise ValueError("Similarity threshold must be between 0 and 1")
            
        self._vector_store.validate()
        self._embedding_model.validate()
