"""Integration tests for the news podcast example.

Tests the complete workflow with real providers and dependencies:
1. End-to-end podcast generation
2. Provider interactions
3. File system operations
4. Cache persistence
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from examples.news_podcast import NewsPodcastGenerator
from pepperpy.core.base import BaseComponent

# Configure test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
def test_output_dir(tmp_path):
    """Provide test output directory."""
    output_dir = tmp_path / "podcasts"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def test_cache_dir(tmp_path):
    """Provide test cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
async def generator(test_output_dir, test_cache_dir):
    """Provide initialized generator with test configuration."""
    # Set test environment
    os.environ["PEPPERPY_CACHE_DIR"] = str(test_cache_dir)

    # Create and initialize generator
    generator = NewsPodcastGenerator(output_dir=test_output_dir)
    await generator.initialize()
    yield generator
    await generator.cleanup()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_workflow(generator):
    """Test complete podcast generation workflow with real providers."""
    # Generate podcast
    output_path = await generator.generate()

    # Verify output file
    assert output_path.exists()
    assert output_path.suffix == ".mp3"
    assert output_path.stat().st_size > 0

    # Verify cache was created
    cache_files = list(Path(os.environ["PEPPERPY_CACHE_DIR"]).glob("*"))
    assert len(cache_files) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_persistence(generator):
    """Test cache persistence across generator instances."""
    # First run - should fetch and cache
    articles1 = await generator.fetch_news()
    assert len(articles1) > 0

    # Second run with new instance - should use cache
    generator2 = NewsPodcastGenerator(output_dir=generator.output_dir)
    await generator2.initialize()
    try:
        articles2 = await generator2.fetch_news()
        assert len(articles2) > 0
        assert articles2 == articles1  # Should get same articles from cache
    finally:
        await generator2.cleanup()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_generation(test_output_dir, test_cache_dir):
    """Test concurrent podcast generation."""

    async def generate_podcast(index: int):
        generator = NewsPodcastGenerator(output_dir=test_output_dir / f"gen{index}")
        await generator.initialize()
        try:
            return await generator.generate()
        finally:
            await generator.cleanup()

    # Create multiple output directories
    for i in range(3):
        (test_output_dir / f"gen{i}").mkdir()

    # Generate podcasts concurrently
    paths = await asyncio.gather(*[generate_podcast(i) for i in range(3)])

    # Verify all podcasts were generated
    assert len(paths) == 3
    for path in paths:
        assert path.exists()
        assert path.suffix == ".mp3"
        assert path.stat().st_size > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_provider_lifecycle(generator):
    """Test provider lifecycle with real implementations."""
    # Verify all providers are initialized
    for provider in [
        generator.content,
        generator.llm,
        generator.memory,
        generator.synthesis,
    ]:
        assert isinstance(provider, BaseComponent)
        assert hasattr(provider, "id")

    # Test cleanup and reinitialization
    await generator.cleanup()
    await generator.initialize()

    # Verify providers still work
    articles = await generator.fetch_news(limit=1)
    assert len(articles) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resource_cleanup(test_output_dir):
    """Test resource cleanup with real providers."""
    generator = None
    try:
        generator = NewsPodcastGenerator(output_dir=test_output_dir)
        await generator.initialize()

        # Simulate error during generation
        with pytest.raises(Exception):
            generator.content.fetch = AsyncMock(
                side_effect=Exception("Simulated error")
            )
            await generator.generate()

    finally:
        if generator:
            await generator.cleanup()

    # Verify output directory is clean
    assert len(list(test_output_dir.glob("*.tmp"))) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_output_file_naming(generator):
    """Test output file naming convention."""
    # Generate multiple podcasts
    paths = []
    for _ in range(2):
        path = await generator.generate()
        paths.append(path)
        await asyncio.sleep(1)  # Ensure different timestamps

    # Verify naming pattern
    for path in paths:
        assert path.name.startswith("podcast_")
        assert path.name.endswith(".mp3")
        # Verify timestamp format
        timestamp = path.stem.split("_")[1]
        datetime.strptime(timestamp, "%Y%m%d_%H%M%S")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_usage(generator):
    """Test memory usage during podcast generation."""
    import psutil

    process = psutil.Process()

    # Measure initial memory
    initial_memory = process.memory_info().rss

    # Generate podcast
    await generator.generate()

    # Measure final memory
    final_memory = process.memory_info().rss

    # Verify memory usage is reasonable (less than 500MB increase)
    memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
    assert memory_increase < 500, f"Memory increase: {memory_increase}MB"
