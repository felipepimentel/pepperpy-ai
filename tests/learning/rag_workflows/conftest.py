"""Test configuration and fixtures for RAG workflow tests."""

import pytest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pepperpy.providers.vector_store.base import VectorIndex, Embeddings
from pepperpy.memory.memory_manager import MemoryManager
from pepperpy.learning.rag_workflows import RAGPipeline, MemoryRetriever
from pepperpy.learning.rag_workflows.pipeline import RetrievalResult

class MockEmbeddings(Embeddings):
    """Mock embeddings for testing."""
    
    async def embed_text(self, text: str) -> List[float]:
        """Mock text embedding.
        
        Args:
            text: Input text
            
        Returns:
            Mock embedding vector
        """
        # Simple deterministic mock embedding
        return [float(ord(c)) for c in text[:10]]
        
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Mock batch embedding.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of mock embedding vectors
        """
        return [await self.embed_text(text) for text in texts]

@pytest.fixture
async def mock_embeddings() -> MockEmbeddings:
    """Create mock embeddings.
    
    Returns:
        Mock embeddings instance
    """
    return MockEmbeddings()

@pytest.fixture
async def vector_index(mock_embeddings: MockEmbeddings) -> VectorIndex:
    """Create vector index with mock embeddings.
    
    Args:
        mock_embeddings: Mock embeddings fixture
        
    Returns:
        Vector index instance
    """
    return VectorIndex(dimension=10)  # Match mock embedding dimension

@pytest.fixture
async def memory_manager(
    tmp_path: Path,
    vector_index: VectorIndex,
    mock_embeddings: MockEmbeddings
) -> MemoryManager:
    """Create memory manager for testing.
    
    Args:
        tmp_path: Pytest temporary path fixture
        vector_index: Vector index fixture
        mock_embeddings: Mock embeddings fixture
        
    Returns:
        Memory manager instance
    """
    return MemoryManager(
        storage_dir=tmp_path / "memory",
        vector_index=vector_index,
        embeddings=mock_embeddings
    )

@pytest.fixture
async def memory_retriever(memory_manager: MemoryManager) -> MemoryRetriever:
    """Create memory retriever for testing.
    
    Args:
        memory_manager: Memory manager fixture
        
    Returns:
        Memory retriever instance
    """
    return MemoryRetriever(
        memory_manager=memory_manager,
        min_similarity=0.7
    )

class MockGenerator:
    """Mock generator for testing."""
    
    def __init__(self, responses: Dict[str, str]):
        """Initialize mock generator.
        
        Args:
            responses: Mapping of prompts to responses
        """
        self.responses = responses
        self.prompts: List[str] = []
        self.contexts: List[List[RetrievalResult]] = []
        
    async def generate(
        self,
        prompt: str,
        context: List[RetrievalResult],
        **kwargs: Any
    ) -> str:
        """Mock generation by returning predefined responses.
        
        Args:
            prompt: Input prompt
            context: Retrieved context
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        self.prompts.append(prompt)
        self.contexts.append(context)
        return self.responses.get(prompt, "")

@pytest.fixture
async def mock_generator() -> MockGenerator:
    """Create mock generator.
    
    Returns:
        Mock generator instance
    """
    responses = {
        "test query": "test response",
        "query1": "response1",
        "query2": "response2"
    }
    return MockGenerator(responses)

@pytest.fixture
async def rag_pipeline(
    memory_retriever: MemoryRetriever,
    mock_generator: MockGenerator
) -> RAGPipeline:
    """Create RAG pipeline for testing.
    
    Args:
        memory_retriever: Memory retriever fixture
        mock_generator: Mock generator fixture
        
    Returns:
        RAG pipeline instance
    """
    return RAGPipeline(
        retriever=memory_retriever,
        generator=mock_generator,
        max_context_length=1000
    ) 