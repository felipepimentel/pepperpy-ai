"""Tests for OpenAI synthesis provider."""

import os
from io import BytesIO
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pepperpy.synthesis.providers.openai import OpenAIProvider

# Sample audio data
SAMPLE_AUDIO = b"test audio data"


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("pepperpy.synthesis.providers.openai.AsyncOpenAI") as mock:
        # Mock speech synthesis
        mock_speech = MagicMock()
        mock_speech.content = SAMPLE_AUDIO
        mock.return_value.audio.speech.create = AsyncMock(return_value=mock_speech)

        yield mock


@pytest.fixture
async def provider(mock_openai) -> AsyncGenerator[OpenAIProvider, None]:
    """Create test provider."""
    provider = OpenAIProvider(api_key="test_key", model="tts-1", voice="alloy")
    yield provider


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory."""
    return tmp_path


@pytest.mark.asyncio
async def test_synthesize(provider, mock_openai):
    """Test speech synthesis."""
    # Test basic synthesis
    audio_data = await provider.synthesize("Test text")
    assert audio_data == SAMPLE_AUDIO

    # Verify API call
    mock_openai.return_value.audio.speech.create.assert_called_once_with(
        model="tts-1", voice="alloy", input="Test text", response_format="mp3"
    )


@pytest.mark.asyncio
async def test_synthesize_with_options(provider, mock_openai):
    """Test synthesis with custom options."""
    # Test with custom options
    await provider.synthesize(
        "Test text", voice="nova", language="pt-BR", output_format="wav"
    )

    # Verify API call
    mock_openai.return_value.audio.speech.create.assert_called_once_with(
        model="tts-1", voice="nova", input="Test text", response_format="wav"
    )


@pytest.mark.asyncio
async def test_save(provider, temp_dir):
    """Test audio file saving."""
    # Generate test audio
    audio_data = await provider.synthesize("Test text")

    # Save to file
    output_path = temp_dir / "test.mp3"
    saved_path = await provider.save(audio_data, output_path)

    # Verify file
    assert saved_path == output_path
    assert saved_path.exists()
    with open(saved_path, "rb") as f:
        assert f.read() == SAMPLE_AUDIO


@pytest.mark.asyncio
async def test_save_with_processors(provider, temp_dir):
    """Test saving with audio processors."""
    # Generate test audio
    audio_data = await provider.synthesize("Test text")

    # Save with processors (not implemented yet)
    output_path = temp_dir / "test.mp3"
    saved_path = await provider.save(
        audio_data, output_path, processors={"normalize": True}
    )

    # Verify file
    assert saved_path == output_path
    assert saved_path.exists()
    with open(saved_path, "rb") as f:
        assert f.read() == SAMPLE_AUDIO


@pytest.mark.asyncio
async def test_stream(provider):
    """Test audio streaming."""
    # Create output stream
    output = BytesIO()

    # Stream audio
    await provider.stream("Test text", output)

    # Verify output
    assert output.getvalue() == SAMPLE_AUDIO


@pytest.mark.asyncio
async def test_stream_with_chunks(provider):
    """Test streaming with custom chunk size."""
    # Create output stream
    output = BytesIO()

    # Stream audio with small chunks
    await provider.stream("Test text", output, chunk_size=4)

    # Verify output
    assert output.getvalue() == SAMPLE_AUDIO


@pytest.mark.asyncio
async def test_api_key_from_env(mock_openai):
    """Test API key loading from environment."""
    # Set environment variable
    os.environ["OPENAI_API_KEY"] = "env_test_key"

    # Create provider without key
    provider = OpenAIProvider()

    # Verify client creation
    mock_openai.assert_called_once_with(api_key="env_test_key")

    # Clean up
    del os.environ["OPENAI_API_KEY"]
