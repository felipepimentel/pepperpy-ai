"""Unit tests for the news podcast example.

Tests individual components of the news podcast generator in isolation:
1. Provider initialization and cleanup
2. News fetching and caching
3. Script generation
4. Audio synthesis
5. Error handling
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from examples.news_podcast import (
    CustomGTTSProvider,
    CustomLocalProvider,
    CustomOpenAIProvider,
    CustomRSSProvider,
    NewsPodcastGenerator,
)
from pepperpy.core.exceptions import ContentError, LLMError, SynthesisError

# Configure test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_rss_provider():
    """Provide mock RSS provider."""
    provider = AsyncMock(spec=CustomRSSProvider)
    provider.fetch.return_value = [
        {
            "title": "Test Article 1",
            "content": "Test content 1",
            "source": "Test Source",
            "published_at": datetime.now(UTC),
            "metadata": {"url": "http://test.com/1"},
        },
        {
            "title": "Test Article 2",
            "content": "Test content 2",
            "source": "Test Source",
            "published_at": datetime.now(UTC),
            "metadata": {"url": "http://test.com/2"},
        },
    ]
    return provider


@pytest.fixture
def mock_llm_provider():
    """Provide mock LLM provider."""
    provider = AsyncMock(spec=CustomOpenAIProvider)
    provider.generate.return_value = {
        "content": "Test podcast script",
        "metadata": {"model": "test-model"},
    }
    return provider


@pytest.fixture
def mock_memory_provider():
    """Provide mock memory provider."""
    provider = AsyncMock(spec=CustomLocalProvider)
    provider.exists.return_value = False
    provider.get.return_value = None
    return provider


@pytest.fixture
def mock_tts_provider():
    """Provide mock TTS provider."""
    provider = AsyncMock(spec=CustomGTTSProvider)
    provider.synthesize.return_value = b"test audio data"
    provider.save.return_value = Path("/tmp/test_podcast.mp3")
    return provider


@pytest.fixture
def generator(
    mock_rss_provider,
    mock_llm_provider,
    mock_memory_provider,
    mock_tts_provider,
    tmp_path,
):
    """Provide configured generator with mock providers."""
    generator = NewsPodcastGenerator(output_dir=tmp_path)
    generator.content = mock_rss_provider
    generator.llm = mock_llm_provider
    generator.memory = mock_memory_provider
    generator.synthesis = mock_tts_provider
    return generator


@pytest.mark.asyncio
async def test_initialization(generator):
    """Test provider initialization."""
    await generator.initialize()

    # Verify all providers were initialized
    generator.content.initialize.assert_called_once()
    generator.llm.initialize.assert_called_once()
    generator.memory.initialize.assert_called_once()
    generator.synthesis.initialize.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup(generator):
    """Test provider cleanup."""
    await generator.cleanup()

    # Verify all providers were cleaned up
    generator.content.cleanup.assert_called_once()
    generator.llm.cleanup.assert_called_once()
    generator.memory.cleanup.assert_called_once()
    generator.synthesis.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_news_cache_miss(generator):
    """Test news fetching when cache is empty."""
    articles = await generator.fetch_news(limit=2)

    # Verify cache was checked
    generator.memory.exists.assert_called_once()
    generator.memory.get.assert_not_called()

    # Verify articles were fetched and cached
    generator.content.fetch.assert_called_once()
    generator.memory.set.assert_called_once()

    assert len(articles) == 2
    assert articles[0]["title"] == "Test Article 1"
    assert articles[1]["title"] == "Test Article 2"


@pytest.mark.asyncio
async def test_fetch_news_cache_hit(generator):
    """Test news fetching when cache exists."""
    # Setup cache hit
    generator.memory.exists.return_value = True
    generator.memory.get.return_value = [{"title": "Cached Article"}]

    articles = await generator.fetch_news()

    # Verify cache was used
    generator.memory.exists.assert_called_once()
    generator.memory.get.assert_called_once()

    # Verify no fetch was performed
    generator.content.fetch.assert_not_called()
    generator.memory.set.assert_not_called()

    assert len(articles) == 1
    assert articles[0]["title"] == "Cached Article"


@pytest.mark.asyncio
async def test_generate_script(generator):
    """Test script generation."""
    articles = [
        {
            "title": "Test Article",
            "content": "Test content",
            "source": "Test Source",
            "published_at": datetime.now(UTC),
            "metadata": {"url": "http://test.com"},
        }
    ]

    script = await generator.generate_script(articles)

    # Verify LLM was called with proper prompt
    generator.llm.generate.assert_called_once()
    prompt = generator.llm.generate.call_args[0][0]
    assert "Você é um locutor de podcast" in prompt
    assert "Test Article" in prompt
    assert "Test content" in prompt

    assert script["content"] == "Test podcast script"


@pytest.mark.asyncio
async def test_create_podcast(generator):
    """Test podcast audio creation."""
    script = {
        "content": "Test podcast script",
        "metadata": {"model": "test-model"},
    }

    output_path = await generator.create_podcast(script)

    # Verify audio was synthesized and saved
    generator.synthesis.synthesize.assert_called_once_with(
        "Test podcast script",
        language="pt-BR",
        voice="onyx",
        normalize=True,
        target_db=-16.0,
        fade_in=0.5,
        fade_out=1.0,
    )
    generator.synthesis.save.assert_called_once()

    assert isinstance(output_path, Path)
    assert str(output_path).endswith(".mp3")


@pytest.mark.asyncio
async def test_generate_complete_workflow(generator):
    """Test complete podcast generation workflow."""
    output_path = await generator.generate()

    # Verify all steps were called
    generator.content.fetch.assert_called_once()
    generator.llm.generate.assert_called_once()
    generator.synthesis.synthesize.assert_called_once()
    generator.synthesis.save.assert_called_once()

    assert isinstance(output_path, Path)
    assert str(output_path).endswith(".mp3")


@pytest.mark.asyncio
async def test_error_handling_no_articles(generator):
    """Test error handling when no articles are found."""
    generator.content.fetch.return_value = []

    with pytest.raises(ValueError, match="No news articles found"):
        await generator.generate()


@pytest.mark.asyncio
async def test_error_handling_content_error(generator):
    """Test error handling for content errors."""
    generator.content.fetch.side_effect = ContentError("Failed to fetch")

    with pytest.raises(ContentError):
        await generator.generate()


@pytest.mark.asyncio
async def test_error_handling_llm_error(generator):
    """Test error handling for LLM errors."""
    generator.llm.generate.side_effect = LLMError("Failed to generate")

    with pytest.raises(LLMError):
        await generator.generate()


@pytest.mark.asyncio
async def test_error_handling_synthesis_error(generator):
    """Test error handling for synthesis errors."""
    generator.synthesis.synthesize.side_effect = SynthesisError("Failed to synthesize")

    with pytest.raises(SynthesisError):
        await generator.generate()


@pytest.mark.asyncio
async def test_validate_output_directory(tmp_path):
    """Test output directory validation."""
    # Test with existing directory
    generator = NewsPodcastGenerator(output_dir=tmp_path)
    generator.validate()  # Should not raise

    # Test with non-existent directory
    bad_path = tmp_path / "nonexistent"
    generator = NewsPodcastGenerator(output_dir=bad_path)
    with pytest.raises(ValueError, match="Output directory does not exist"):
        generator.validate()


@pytest.mark.asyncio
async def test_resource_cleanup_on_error(generator):
    """Test resource cleanup when an error occurs."""
    generator.content.fetch.side_effect = ContentError("Test error")

    try:
        await generator.generate()
    except ContentError:
        pass

    # Verify cleanup was still performed
    generator.content.cleanup.assert_called_once()
    generator.llm.cleanup.assert_called_once()
    generator.memory.cleanup.assert_called_once()
    generator.synthesis.cleanup.assert_called_once()
