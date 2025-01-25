"""Tests for text processing tools."""

import pytest

from pepperpy.tools.text import TextChunkerTool


@pytest.fixture
def chunker():
    """Create a text chunker tool."""
    return TextChunkerTool(chunk_size=10, overlap=2)


async def test_chunker_initialization(chunker):
    """Test chunker initialization."""
    assert chunker.name == "text_chunker"
    assert chunker.description == "Split text into overlapping chunks"
    assert not chunker.is_initialized
    assert chunker._chunk_size == 10
    assert chunker._overlap == 2


async def test_chunker_lifecycle(chunker):
    """Test chunker lifecycle."""
    # Test initialization
    await chunker.initialize()
    assert chunker.is_initialized
    
    # Test cleanup
    await chunker.cleanup()
    assert not chunker.is_initialized


async def test_chunker_validation(chunker):
    """Test chunker validation."""
    chunker.validate()  # Should not raise


@pytest.mark.parametrize("input_text,expected_chunks", [
    # Empty text
    ("", []),
    
    # Text shorter than chunk size
    ("Hello", ["Hello"]),
    
    # Text exactly chunk size
    ("0123456789", ["0123456789"]),
    
    # Text longer than chunk size, breaks at space
    ("Hello world test", ["Hello", "d test"]),
    
    # Text with no spaces
    ("01234567890123", ["0123456789", "890123"]),
])
async def test_chunker_execute(chunker, input_text, expected_chunks):
    """Test chunker execution with various inputs."""
    await chunker.initialize()
    try:
        result = await chunker.execute(input_text)
        assert result == expected_chunks
    finally:
        await chunker.cleanup()


async def test_chunker_invalid_input(chunker):
    """Test chunker with invalid input."""
    await chunker.initialize()
    try:
        with pytest.raises(ValueError, match="Input must be a string"):
            await chunker.execute(123)
    finally:
        await chunker.cleanup()


async def test_chunker_invalid_params():
    """Test chunker with invalid parameters."""
    # Test invalid chunk size
    with pytest.raises(ValueError, match="Chunk size must be positive"):
        chunker = TextChunkerTool(chunk_size=0)
        await chunker.execute("test")
    
    # Test invalid overlap
    with pytest.raises(ValueError, match="Overlap must be non-negative"):
        chunker = TextChunkerTool(chunk_size=10, overlap=-1)
        await chunker.execute("test")
    
    # Test overlap >= chunk size
    with pytest.raises(ValueError, match="Overlap must be less than chunk size"):
        chunker = TextChunkerTool(chunk_size=10, overlap=10)
        await chunker.execute("test")


async def test_chunker_context_params(chunker):
    """Test chunker with context parameters."""
    await chunker.initialize()
    try:
        text = "Hello world this is a test"
        context = {"chunk_size": 5, "overlap": 1}
        result = await chunker.execute(text, context)
        assert len(result) > 0
        assert all(len(chunk) <= 5 for chunk in result)
    finally:
        await chunker.cleanup() 