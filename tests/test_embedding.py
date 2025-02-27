"""Tests for the embedding module."""

from pathlib import Path

import numpy as np
import pytest

from pepperpy.rag.embedding import (
    DocumentEmbedder,
    SentenceEmbedder,
    TextEmbedder,
)


@pytest.mark.asyncio
async def test_text_embedder_initialization():
    """Test text embedder initialization."""
    embedder = TextEmbedder(model_name="all-MiniLM-L6-v2")
    assert embedder.model_name == "all-MiniLM-L6-v2"
    assert embedder.model is None


@pytest.mark.asyncio
async def test_text_embedder_with_sample_text():
    """Test text embedder with sample text."""
    embedder = TextEmbedder()
    await embedder.initialize()

    with open(Path(__file__).parent / "data" / "sample1.txt", "r") as f:
        text = f.read()

    embedding = await embedder.embed(text)

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1, 384)  # Default embedding dimension
    assert not np.allclose(embedding, 0)  # Embeddings should not be all zeros

    await embedder.cleanup()


@pytest.mark.asyncio
async def test_document_embedder():
    """Test document embedder functionality."""
    embedder = DocumentEmbedder()
    await embedder.initialize()

    with open(Path(__file__).parent / "data" / "sample2.txt", "r") as f:
        text = f.read()

    embedding = await embedder.embed(text)

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1, 768)  # MPNet base embedding dimension
    assert not np.allclose(embedding, 0)

    await embedder.cleanup()


@pytest.mark.asyncio
async def test_sentence_embedder():
    """Test sentence embedder functionality."""
    embedder = SentenceEmbedder()
    await embedder.initialize()

    sentences = [
        "This is the first sentence.",
        "This is the second sentence.",
        "This is the third sentence.",
    ]

    embeddings = await embedder.embed(sentences)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (3, 384)  # (n_sentences, embedding_dim)
    assert not np.allclose(embeddings, 0)

    await embedder.cleanup()


@pytest.mark.asyncio
async def test_embedder_batch_processing():
    """Test embedders with batch processing."""
    embedders = [
        TextEmbedder(),
        DocumentEmbedder(),
        SentenceEmbedder(),
    ]

    texts = []
    for i in range(1, 4):
        with open(Path(__file__).parent / "data" / f"sample{i}.txt", "r") as f:
            texts.append(f.read())

    for embedder in embedders:
        await embedder.initialize()
        embeddings = await embedder.embed(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == len(texts)
        assert not np.allclose(embeddings, 0)

        await embedder.cleanup()


@pytest.mark.asyncio
async def test_embedder_empty_input():
    """Test embedders with empty input."""
    embedders = [
        TextEmbedder(),
        DocumentEmbedder(),
        SentenceEmbedder(),
    ]

    for embedder in embedders:
        await embedder.initialize()

        with pytest.raises(ValueError):
            await embedder.embed("")

        with pytest.raises(ValueError):
            await embedder.embed([])

        await embedder.cleanup()


@pytest.mark.asyncio
async def test_embedder_similarity():
    """Test embedding similarity computation."""
    embedder = TextEmbedder()
    await embedder.initialize()

    text1 = "This is a document about machine learning."
    text2 = "This text discusses artificial intelligence."
    text3 = "The weather is nice today."

    emb1 = await embedder.embed(text1)
    emb2 = await embedder.embed(text2)
    emb3 = await embedder.embed(text3)

    # Compute cosine similarities
    sim12 = np.dot(emb1[0], emb2[0]) / (
        np.linalg.norm(emb1[0]) * np.linalg.norm(emb2[0])
    )
    sim13 = np.dot(emb1[0], emb3[0]) / (
        np.linalg.norm(emb1[0]) * np.linalg.norm(emb3[0])
    )
    sim23 = np.dot(emb2[0], emb3[0]) / (
        np.linalg.norm(emb2[0]) * np.linalg.norm(emb3[0])
    )

    # Similar texts should have higher similarity
    assert sim12 > sim13
    assert sim12 > sim23

    await embedder.cleanup()
