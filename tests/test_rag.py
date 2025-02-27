"""Tests for the RAG module."""

import numpy as np
import pytest

from pepperpy.rag.chunking import TextChunker
from pepperpy.rag.embedding import TextEmbedder
from pepperpy.rag.indexing import VectorIndexer
from pepperpy.rag.retrieval import VectorRetriever


@pytest.mark.asyncio
async def test_text_chunker():
    """Test text chunking functionality."""
    chunker = TextChunker(chunk_size=10, overlap=2)
    text = "This is a test document for chunking."
    chunks = await chunker.chunk(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert all(len(chunk) <= 10 for chunk in chunks)


@pytest.mark.asyncio
async def test_text_embedder():
    """Test text embedding functionality."""
    embedder = TextEmbedder()
    await embedder.initialize()

    text = "This is a test document."
    embedding = await embedder.embed(text)

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1, 384)  # Default embedding dimension

    await embedder.cleanup()


@pytest.mark.asyncio
async def test_vector_indexer():
    """Test vector indexing functionality."""
    indexer = VectorIndexer()
    await indexer.initialize()

    embeddings = np.random.rand(3, 384)  # 3 documents with 384-dim embeddings
    metadata = [{"id": i} for i in range(3)]
    await indexer.index(embeddings, metadata)

    query = np.random.rand(384)
    results = await indexer.search(query, k=2)

    assert len(results) == 2
    assert all(isinstance(result, dict) for result in results)

    await indexer.cleanup()


@pytest.mark.asyncio
async def test_vector_retriever():
    """Test vector retrieval functionality."""
    embedder = TextEmbedder()
    indexer = VectorIndexer()
    retriever = VectorRetriever(embedder=embedder, indexer=indexer)

    await retriever.initialize()

    documents = ["First document", "Second document", "Third document"]
    embeddings = await embedder.embed(documents)
    await indexer.index(embeddings, metadata=[{"id": i} for i in range(len(documents))])

    results = await retriever.retrieve("test query", k=2)

    assert len(results) == 2
    assert all(isinstance(result, dict) for result in results)

    await retriever.cleanup()
