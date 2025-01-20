"""Tests for RAG evaluator functionality."""

import pytest
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

from pepperpy.learning.rag_workflows.pipeline import RAGPipeline
from pepperpy.learning.rag_workflows.evaluator import RAGEvaluator, EvaluationMetrics

class MockPipeline(RAGPipeline):
    """Mock RAG pipeline for testing."""
    
    def __init__(self, responses: List[Dict[str, Any]]):
        """Initialize mock pipeline.
        
        Args:
            responses: List of predefined responses
        """
        self.responses = responses
        self.queries: List[str] = []
        
    async def process(
        self,
        query: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Mock processing by returning predefined responses.
        
        Args:
            query: Input query
            **kwargs: Additional parameters
            
        Returns:
            Processing result
        """
        self.queries.append(query)
        for response in self.responses:
            if response.get("query") == query:
                return response
        return {
            "response": "",
            "context": [],
            "metadata": {}
        }
        
    async def batch_process(
        self,
        queries: List[str],
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Mock batch processing.
        
        Args:
            queries: List of queries
            **kwargs: Additional parameters
            
        Returns:
            List of processing results
        """
        return [await self.process(q, **kwargs) for q in queries]

@pytest.mark.asyncio
async def test_evaluate():
    """Test evaluating RAG pipeline performance."""
    # Setup mock pipeline with test responses
    mock_responses = [
        {
            "query": "test query 1",
            "response": "test response 1",
            "context": [
                {"source_id": "1", "content": "relevant content 1"},
                {"source_id": "2", "content": "relevant content 2"}
            ],
            "metadata": {"timestamp": datetime.utcnow().isoformat()}
        },
        {
            "query": "test query 2",
            "response": "test response 2",
            "context": [
                {"source_id": "3", "content": "relevant content 3"}
            ],
            "metadata": {"timestamp": datetime.utcnow().isoformat()}
        }
    ]
    
    pipeline = MockPipeline(mock_responses)
    evaluator = RAGEvaluator(pipeline)
    
    # Create test cases
    test_cases = [
        {
            "query": "test query 1",
            "expected_response": "expected response 1",
            "relevant_context": ["1", "2"]
        },
        {
            "query": "test query 2",
            "expected_response": "expected response 2",
            "relevant_context": ["3"]
        }
    ]
    
    # Test evaluation
    results = await evaluator.evaluate(test_cases)
    
    # Verify evaluation results
    assert "overall_metrics" in results
    assert "individual_metrics" in results
    assert "timestamp" in results
    
    # Verify metrics
    metrics = results["overall_metrics"]
    assert all(0 <= metrics[key] <= 1 for key in [
        "avg_precision",
        "avg_recall",
        "avg_quality",
        "avg_relevance"
    ])
    assert metrics["avg_latency"] >= 0
    
    # Verify individual metrics
    assert len(results["individual_metrics"]) == len(test_cases)
    for metric in results["individual_metrics"]:
        assert isinstance(metric, EvaluationMetrics)
        assert 0 <= metric.retrieval_precision <= 1
        assert 0 <= metric.retrieval_recall <= 1
        assert 0 <= metric.response_quality <= 1
        assert 0 <= metric.context_relevance <= 1
        assert metric.latency >= 0

@pytest.mark.asyncio
async def test_evaluate_empty_context():
    """Test evaluation with empty context."""
    # Setup mock pipeline with empty context
    mock_responses = [
        {
            "query": "test query",
            "response": "test response",
            "context": [],
            "metadata": {"timestamp": datetime.utcnow().isoformat()}
        }
    ]
    
    pipeline = MockPipeline(mock_responses)
    evaluator = RAGEvaluator(pipeline)
    
    # Create test case
    test_cases = [
        {
            "query": "test query",
            "expected_response": "expected response",
            "relevant_context": ["1"]  # Expected but not retrieved
        }
    ]
    
    # Test evaluation
    results = await evaluator.evaluate(test_cases)
    
    # Verify metrics with empty context
    metrics = results["individual_metrics"][0]
    assert metrics.retrieval_precision == 0  # No retrieved context
    assert metrics.retrieval_recall == 0  # No relevant context found
    assert metrics.context_relevance == 0  # No context to evaluate

@pytest.mark.asyncio
async def test_evaluate_perfect_match():
    """Test evaluation with perfect matching results."""
    # Setup mock pipeline with perfect matches
    mock_responses = [
        {
            "query": "test query",
            "response": "expected response",  # Exact match
            "context": [
                {"source_id": "1", "content": "relevant content"}
            ],
            "metadata": {"timestamp": datetime.utcnow().isoformat()}
        }
    ]
    
    pipeline = MockPipeline(mock_responses)
    evaluator = RAGEvaluator(pipeline)
    
    # Create test case
    test_cases = [
        {
            "query": "test query",
            "expected_response": "expected response",  # Exact match
            "relevant_context": ["1"]  # All relevant context found
        }
    ]
    
    # Test evaluation
    results = await evaluator.evaluate(test_cases)
    
    # Verify perfect metrics
    metrics = results["individual_metrics"][0]
    assert metrics.retrieval_precision == 1.0
    assert metrics.retrieval_recall == 1.0
    assert metrics.response_quality == 1.0  # Perfect response match

@pytest.mark.asyncio
async def test_evaluate_multiple_contexts():
    """Test evaluation with multiple context items."""
    # Setup mock pipeline with multiple contexts
    mock_responses = [
        {
            "query": "test query",
            "response": "test response",
            "context": [
                {"source_id": "1", "content": "relevant content 1"},
                {"source_id": "2", "content": "relevant content 2"},
                {"source_id": "3", "content": "irrelevant content"}
            ],
            "metadata": {"timestamp": datetime.utcnow().isoformat()}
        }
    ]
    
    pipeline = MockPipeline(mock_responses)
    evaluator = RAGEvaluator(pipeline)
    
    # Create test case
    test_cases = [
        {
            "query": "test query",
            "expected_response": "test response",
            "relevant_context": ["1", "2"]  # Only 2 of 3 are relevant
        }
    ]
    
    # Test evaluation
    results = await evaluator.evaluate(test_cases)
    
    # Verify metrics with partial matches
    metrics = results["individual_metrics"][0]
    assert metrics.retrieval_precision == 2/3  # 2 relevant out of 3 retrieved
    assert metrics.retrieval_recall == 1.0  # All relevant contexts found 