"""Tests for the chunking module."""

from pathlib import Path

import pytest

from pepperpy.rag.chunking import (
    ParagraphChunker,
    SentenceChunker,
    TextChunker,
    TokenChunker,
)


@pytest.mark.asyncio
async def test_text_chunker_initialization():
    """Test text chunker initialization."""
    chunker = TextChunker(chunk_size=100, overlap=20)
    assert chunker.chunk_size == 100
    assert chunker.overlap == 20


@pytest.mark.asyncio
async def test_text_chunker_with_sample_text():
    """Test text chunker with sample text."""
    chunker = TextChunker(chunk_size=50, overlap=10)
    await chunker.initialize()

    with open(Path(__file__).parent / "data" / "sample1.txt") as f:
        text = f.read()

    chunks = await chunker.chunk(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert all(len(chunk) <= 50 for chunk in chunks)

    # Check overlap
    for i in range(len(chunks) - 1):
        overlap_text = chunks[i][-10:]
        assert any(chunk.startswith(overlap_text) for chunk in chunks[i + 1 :])

    await chunker.cleanup()


@pytest.mark.asyncio
async def test_token_chunker():
    """Test token chunker functionality."""
    chunker = TokenChunker(max_tokens=10, overlap_tokens=2)
    await chunker.initialize()

    text = "This is a test sentence for token-based chunking."
    chunks = await chunker.chunk(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)

    await chunker.cleanup()


@pytest.mark.asyncio
async def test_sentence_chunker():
    """Test sentence chunker functionality."""
    chunker = SentenceChunker(max_sentences=2)
    await chunker.initialize()

    text = "This is the first sentence. This is the second sentence. This is the third sentence."
    chunks = await chunker.chunk(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert all(
        len(chunk.split(".")) <= 3 for chunk in chunks
    )  # 2 sentences + possible empty string

    await chunker.cleanup()


@pytest.mark.asyncio
async def test_paragraph_chunker():
    """Test paragraph chunker functionality."""
    chunker = ParagraphChunker(max_paragraphs=2)
    await chunker.initialize()

    with open(Path(__file__).parent / "data" / "sample2.txt") as f:
        text = f.read()

    chunks = await chunker.chunk(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert all(len(chunk.split("\n\n")) <= 2 for chunk in chunks)

    await chunker.cleanup()


@pytest.mark.asyncio
async def test_chunker_empty_text():
    """Test chunkers with empty text."""
    chunkers = [
        TextChunker(chunk_size=50, overlap=10),
        TokenChunker(max_tokens=10, overlap_tokens=2),
        SentenceChunker(max_sentences=2),
        ParagraphChunker(max_paragraphs=2),
    ]

    for chunker in chunkers:
        await chunker.initialize()
        chunks = await chunker.chunk("")
        assert len(chunks) == 0
        await chunker.cleanup()


@pytest.mark.asyncio
async def test_chunker_single_chunk():
    """Test chunkers with text smaller than chunk size."""
    text = "This is a short text."
    chunkers = [
        TextChunker(chunk_size=100, overlap=10),
        TokenChunker(max_tokens=20, overlap_tokens=2),
        SentenceChunker(max_sentences=5),
        ParagraphChunker(max_paragraphs=5),
    ]

    for chunker in chunkers:
        await chunker.initialize()
        chunks = await chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0] == text
        await chunker.cleanup()
