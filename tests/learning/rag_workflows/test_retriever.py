"""Tests for memory-based retriever functionality."""

import pytest
from datetime import datetime
from typing import Any, Dict, List, Optional

from pepperpy.memory.memory_manager import MemoryManager
from pepperpy.learning.rag_workflows import MemoryRetriever

@pytest.mark.asyncio
async def test_retrieve(memory_manager: MemoryManager):
    """Test retrieving content from memory."""
    # Initialize retriever
    retriever = MemoryRetriever(
        memory_manager=memory_manager,
        min_similarity=0.7
    )
    
    # Add test memories
    await memory_manager.store_memory(
        memory_id="test1",
        data={"text": "test content 1"},
        metadata={"source": "doc1"},
        text="test content 1"
    )
    await memory_manager.store_memory(
        memory_id="test2",
        data={"text": "test content 2"},
        metadata={"source": "doc2"},
        text="test content 2"
    )
    
    # Test retrieval
    results = await retriever.retrieve(
        query="test query",
        k=2
    )
    
    # Verify results
    assert len(results) == 2
    assert all(isinstance(r.content, str) for r in results)
    assert all(isinstance(r.metadata, dict) for r in results)
    assert all(isinstance(r.score, float) for r in results)
    assert all(isinstance(r.source_id, str) for r in results)
    assert all(isinstance(r.retrieved_at, datetime) for r in results)

@pytest.mark.asyncio
async def test_retrieve_with_filter(memory_manager: MemoryManager):
    """Test retrieving content with metadata filter."""
    # Initialize retriever
    retriever = MemoryRetriever(
        memory_manager=memory_manager,
        min_similarity=0.7
    )
    
    # Add test memories with different sources
    await memory_manager.store_memory(
        memory_id="test1",
        data={"text": "test content 1"},
        metadata={"source": "doc1"},
        text="test content 1"
    )
    await memory_manager.store_memory(
        memory_id="test2",
        data={"text": "test content 2"},
        metadata={"source": "doc2"},
        text="test content 2"
    )
    
    # Test retrieval with filter
    results = await retriever.retrieve(
        query="test query",
        k=2,
        filter={"source": "doc1"}
    )
    
    # Verify filtered results
    assert len(results) == 1
    assert results[0].metadata["source"] == "doc1"

@pytest.mark.asyncio
async def test_retrieve_with_similarity_threshold(memory_manager: MemoryManager):
    """Test retrieving content with similarity threshold."""
    # Initialize retriever with high threshold
    retriever = MemoryRetriever(
        memory_manager=memory_manager,
        min_similarity=0.9  # High threshold
    )
    
    # Add test memories
    await memory_manager.store_memory(
        memory_id="test1",
        data={"text": "test content"},
        metadata={"score": 0.95},  # High similarity
        text="test content"
    )
    await memory_manager.store_memory(
        memory_id="test2",
        data={"text": "test content"},
        metadata={"score": 0.85},  # Below threshold
        text="test content"
    )
    
    # Test retrieval
    results = await retriever.retrieve(
        query="test query",
        k=2
    )
    
    # Verify threshold filtering
    assert len(results) == 1  # Only one result above threshold
    assert results[0].score >= 0.9

@pytest.mark.asyncio
async def test_retrieve_empty_memory(memory_manager: MemoryManager):
    """Test retrieving from empty memory."""
    # Initialize retriever
    retriever = MemoryRetriever(
        memory_manager=memory_manager,
        min_similarity=0.7
    )
    
    # Test retrieval with no stored memories
    results = await retriever.retrieve(
        query="test query",
        k=2
    )
    
    # Verify empty results
    assert len(results) == 0

@pytest.mark.asyncio
async def test_retrieve_limit(memory_manager: MemoryManager):
    """Test retrieval limit."""
    # Initialize retriever
    retriever = MemoryRetriever(
        memory_manager=memory_manager,
        min_similarity=0.7
    )
    
    # Add multiple test memories
    for i in range(5):
        await memory_manager.store_memory(
            memory_id=f"test{i}",
            data={"text": f"test content {i}"},
            metadata={"index": i},
            text=f"test content {i}"
        )
    
    # Test retrieval with limit
    results = await retriever.retrieve(
        query="test query",
        k=3  # Limit to 3 results
    )
    
    # Verify result limit
    assert len(results) == 3 