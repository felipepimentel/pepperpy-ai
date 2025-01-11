"""Tests for the RAG module."""

import pytest
from typing import Any, Dict, List, Optional

from pepperpy_ai.capabilities.rag.base import Document, RAGConfig
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse


@pytest.fixture
def simple_rag_config():
    """Fixture that provides a simple RAG config."""
    return RAGConfig(
        name="test_rag",
        description="Test RAG capability",
        prompt_template=(
            "Based on the following documents:\n\n{documents}\n\n"
            "Please answer the following question:\n\n{query}"
        ),
        max_documents=5,
    )


@pytest.mark.asyncio
async def test_rag_document_operations(
    simple_rag_config: RAGConfig,
    mock_provider: BaseProvider,
):
    """Test RAG document operations."""
    # Skip test if numpy/sentence-transformers not available
    pytest.importorskip("numpy")
    pytest.importorskip("sentence_transformers")
    
    from pepperpy_ai.capabilities.rag.simple import SimpleRAG
    
    rag = SimpleRAG(simple_rag_config, mock_provider)
    await rag.initialize()
    
    # Create test documents
    docs = [
        Document(
            id=f"doc{i}",
            content=f"Test document {i}",
            metadata={"source": "test"},
        )
        for i in range(3)
    ]
    
    # Test adding documents
    for doc in docs:
        await rag.add_document(doc)
    
    # Test searching
    results = await rag.search("test", limit=2)
    assert len(results) == 2
    assert all(isinstance(doc, Document) for doc in results)
    
    # Test removing documents
    await rag.remove_document(docs[0].id)
    results = await rag.search("test")
    assert docs[0].id not in [doc.id for doc in results]
    
    # Test clearing
    await rag.clear()
    results = await rag.search("test")
    assert len(results) == 0
    
    await rag.cleanup()


@pytest.mark.asyncio
async def test_rag_generation(
    simple_rag_config: RAGConfig,
    mock_provider: BaseProvider,
):
    """Test RAG response generation."""
    # Skip test if numpy/sentence-transformers not available
    pytest.importorskip("numpy")
    pytest.importorskip("sentence_transformers")
    
    from pepperpy_ai.capabilities.rag.simple import SimpleRAG
    
    rag = SimpleRAG(simple_rag_config, mock_provider)
    await rag.initialize()
    
    # Add test documents
    docs = [
        Document(
            id=f"doc{i}",
            content=f"Test document {i}",
            metadata={"source": "test"},
        )
        for i in range(3)
    ]
    for doc in docs:
        await rag.add_document(doc)
    
    # Test normal generation
    response = await rag.generate("What are the test documents about?")
    assert isinstance(response, AIResponse)
    assert response.content == "Mock completion"
    
    # Test streaming generation
    response = await rag.generate("What are the test documents about?", stream=True)
    assert isinstance(response, AIResponse)
    assert response.content == "Mock stream"
    
    await rag.cleanup()


@pytest.mark.asyncio
async def test_rag_empty_state(
    simple_rag_config: RAGConfig,
    mock_provider: BaseProvider,
):
    """Test RAG behavior with no documents."""
    # Skip test if numpy/sentence-transformers not available
    pytest.importorskip("numpy")
    pytest.importorskip("sentence_transformers")
    
    from pepperpy_ai.capabilities.rag.simple import SimpleRAG
    
    rag = SimpleRAG(simple_rag_config, mock_provider)
    await rag.initialize()
    
    # Search with no documents
    results = await rag.search("test query")
    assert len(results) == 0
    
    # Generate with no documents
    response = await rag.generate("test query")
    assert isinstance(response, AIResponse)
    assert response.content == "Mock completion"
    
    await rag.cleanup() 