"""Test configuration and fixtures for learning module tests."""

import pytest
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List

from pepperpy.llms.base_llm import BaseLLM
from pepperpy.memory.memory_manager import MemoryManager
from pepperpy.providers.vector_store.base import VectorIndex, Embeddings
from pepperpy.learning.examples import ExampleStore, ExampleManager
from pepperpy.learning.strategies import InContextLearner, RetrievalLearner

class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def __init__(self, responses: Dict[str, str]):
        """Initialize mock LLM.
        
        Args:
            responses: Mapping of prompts to responses
        """
        self.responses = responses
        self.prompts: List[str] = []
        
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Mock generation by returning predefined responses.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Predefined response or empty string
        """
        self.prompts.append(prompt)
        return self.responses.get(prompt, "")

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
async def temp_dir(tmp_path: Path) -> Path:
    """Create temporary directory for tests.
    
    Args:
        tmp_path: Pytest temporary path fixture
        
    Returns:
        Path to temporary directory
    """
    test_dir = tmp_path / "test_learning"
    test_dir.mkdir()
    return test_dir

@pytest.fixture
async def mock_llm() -> MockLLM:
    """Create mock LLM with predefined responses.
    
    Returns:
        Mock LLM instance
    """
    responses = {
        "Test prompt": "Test response",
        "Use the following examples to understand the task format:\n\nInput: test\nOutput: result\n---\n\nNow, process this input:\ntest query": "test result",
    }
    return MockLLM(responses)

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
    temp_dir: Path,
    vector_index: VectorIndex,
    mock_embeddings: MockEmbeddings
) -> AsyncGenerator[MemoryManager, None]:
    """Create memory manager for testing.
    
    Args:
        temp_dir: Temporary directory fixture
        vector_index: Vector index fixture
        mock_embeddings: Mock embeddings fixture
        
    Yields:
        Memory manager instance
    """
    manager = MemoryManager(
        storage_dir=temp_dir / "memory",
        vector_index=vector_index,
        embeddings=mock_embeddings
    )
    yield manager
    # Clean up resources after test
    await vector_index.clear()

@pytest.fixture
async def example_store(temp_dir: Path) -> ExampleStore:
    """Create example store for testing.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Example store instance
    """
    return ExampleStore(storage_dir=temp_dir / "examples")

@pytest.fixture
async def example_manager(example_store: ExampleStore) -> ExampleManager:
    """Create example manager for testing.
    
    Args:
        example_store: Example store fixture
        
    Returns:
        Example manager instance
    """
    return ExampleManager(store=example_store)

@pytest.fixture
async def in_context_learner(
    mock_llm: MockLLM,
    example_manager: ExampleManager
) -> InContextLearner:
    """Create in-context learner for testing.
    
    Args:
        mock_llm: Mock LLM fixture
        example_manager: Example manager fixture
        
    Returns:
        In-context learner instance
    """
    return InContextLearner(
        llm=mock_llm,
        example_manager=example_manager
    )

@pytest.fixture
async def retrieval_learner(
    mock_llm: MockLLM,
    memory_manager: MemoryManager,
    example_manager: ExampleManager
) -> RetrievalLearner:
    """Create retrieval learner for testing.
    
    Args:
        mock_llm: Mock LLM fixture
        memory_manager: Memory manager fixture
        example_manager: Example manager fixture
        
    Returns:
        Retrieval learner instance
    """
    return RetrievalLearner(
        llm=mock_llm,
        memory_manager=memory_manager,
        example_manager=example_manager
    ) 