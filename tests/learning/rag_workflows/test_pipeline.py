"""Tests for RAG pipeline functionality."""

import pytest
from datetime import datetime
from typing import Any, Dict, List, Optional

from pepperpy.learning.rag_workflows.pipeline import RAGPipeline, RetrievalResult

class MockRetriever:
    """Mock retriever for testing."""
    
    def __init__(self, results: List[Dict[str, Any]]):
        """Initialize mock retriever.
        
        Args:
            results: List of predefined results
        """
        self.results = results
        self.queries: List[str] = []
        
    async def retrieve(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Mock retrieval by returning predefined results.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of retrieval results
        """
        self.queries.append(query)
        return [
            RetrievalResult(
                content=r["content"],
                metadata=r.get("metadata", {}),
                score=r.get("score", 1.0),
                source_id=r.get("source_id", "test"),
                retrieved_at=datetime.utcnow()
            )
            for r in self.results[:k]
        ]

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

@pytest.mark.asyncio
async def test_process():
    """Test processing a query through the RAG pipeline."""
    # Setup mock components
    mock_results = [
        {
            "content": "test content 1",
            "metadata": {"source": "doc1"},
            "score": 0.9,
            "source_id": "1"
        },
        {
            "content": "test content 2",
            "metadata": {"source": "doc2"},
            "score": 0.8,
            "source_id": "2"
        }
    ]
    mock_responses = {
        "test query": "test response"
    }
    
    retriever = MockRetriever(mock_results)
    generator = MockGenerator(mock_responses)
    pipeline = RAGPipeline(
        retriever=retriever,
        generator=generator,
        max_context_length=1000
    )
    
    # Test processing
    result = await pipeline.process(
        query="test query",
        k=2
    )
    
    # Verify retrieval
    assert len(retriever.queries) == 1
    assert retriever.queries[0] == "test query"
    
    # Verify generation
    assert len(generator.prompts) == 1
    assert generator.prompts[0] == "test query"
    assert len(generator.contexts) == 1
    assert len(generator.contexts[0]) == 2
    
    # Verify result
    assert result["response"] == "test response"
    assert len(result["context"]) == 2
    assert result["metadata"]["num_context"] == 2
    assert "timestamp" in result["metadata"]
    assert "total_context_length" in result["metadata"]

@pytest.mark.asyncio
async def test_context_length_limit():
    """Test context length limiting in the RAG pipeline."""
    # Setup mock components with long content
    mock_results = [
        {
            "content": "a" * 800,  # Long content
            "score": 0.9,
            "source_id": "1"
        },
        {
            "content": "b" * 800,  # Long content
            "score": 0.8,
            "source_id": "2"
        }
    ]
    
    retriever = MockRetriever(mock_results)
    generator = MockGenerator({"test": "response"})
    pipeline = RAGPipeline(
        retriever=retriever,
        generator=generator,
        max_context_length=1000  # Only allow ~1 long content
    )
    
    # Test processing
    result = await pipeline.process(
        query="test",
        k=2
    )
    
    # Verify context length limiting
    assert len(result["context"]) == 1  # Only one content should fit
    assert result["metadata"]["total_context_length"] <= 1000

@pytest.mark.asyncio
async def test_batch_process():
    """Test batch processing through the RAG pipeline."""
    # Setup mock components
    mock_results = [
        {
            "content": "test content",
            "score": 0.9,
            "source_id": "1"
        }
    ]
    mock_responses = {
        "query1": "response1",
        "query2": "response2"
    }
    
    retriever = MockRetriever(mock_results)
    generator = MockGenerator(mock_responses)
    pipeline = RAGPipeline(
        retriever=retriever,
        generator=generator
    )
    
    # Test batch processing
    queries = ["query1", "query2"]
    results = await pipeline.batch_process(queries)
    
    # Verify results
    assert len(results) == 2
    assert results[0]["response"] == "response1"
    assert results[1]["response"] == "response2"
    
    # Verify retrieval and generation calls
    assert len(retriever.queries) == 2
    assert len(generator.prompts) == 2

@pytest.mark.asyncio
async def test_empty_context():
    """Test pipeline behavior with no relevant context."""
    # Setup mock components with no results
    retriever = MockRetriever([])
    generator = MockGenerator({"test": "fallback response"})
    pipeline = RAGPipeline(
        retriever=retriever,
        generator=generator
    )
    
    # Test processing
    result = await pipeline.process("test")
    
    # Verify handling of empty context
    assert result["response"] == "fallback response"
    assert len(result["context"]) == 0
    assert result["metadata"]["num_context"] == 0 